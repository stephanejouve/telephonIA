"""Tests pour les routes API web."""

import io
import os
import signal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydub.generators import Sine

from telephonia.web.api import state
from telephonia.web.app import create_app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Reinitialise l'etat entre chaque test."""
    from telephonia.config import get_default_messages

    state.messages = get_default_messages(music_path=state.music_path)
    state.voice_id = None
    state.prefix = ""
    state.imported_g729 = set()
    yield


class TestHealth:
    """Tests pour GET /api/health."""

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestGetMessages:
    """Tests pour GET /api/messages."""

    def test_get_messages_returns_three(self, client):
        response = client.get("/api/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_messages_names(self, client):
        response = client.get("/api/messages")
        data = response.json()
        names = [m["name"] for m in data]
        assert names == ["pre_decroche", "attente", "repondeur"]

    def test_get_messages_fields(self, client):
        response = client.get("/api/messages")
        data = response.json()
        for msg in data:
            assert "name" in msg
            assert "label" in msg
            assert "description" in msg
            assert "text" in msg
            assert "has_music" in msg
            assert "has_audio" in msg
            assert isinstance(msg["text"], str)
            assert len(msg["text"]) > 0


class TestUpdateMessage:
    """Tests pour PUT /api/messages/{name}."""

    def test_update_message_text(self, client):
        new_text = "Nouveau texte de test"
        response = client.put(
            "/api/messages/pre_decroche",
            json={"text": new_text},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == new_text
        assert data["name"] == "pre_decroche"

    def test_update_message_persists(self, client):
        new_text = "Texte modifie"
        client.put("/api/messages/attente", json={"text": new_text})

        response = client.get("/api/messages")
        data = response.json()
        attente = next(m for m in data if m["name"] == "attente")
        assert attente["text"] == new_text

    def test_update_message_not_found(self, client):
        response = client.put(
            "/api/messages/inexistant",
            json={"text": "texte"},
        )
        assert response.status_code == 404


class TestJsonPersistence:
    """Tests pour la persistance JSON des messages."""

    def test_save_messages_creates_json(self, client, tmp_path):
        """PUT message → fichier JSON cree."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            client.put("/api/messages/pre_decroche", json={"text": "Texte perso"})

            json_path = os.path.join(str(tmp_path), "messages.json")
            assert os.path.exists(json_path)

            import json

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["pre_decroche"] == "Texte perso"
        finally:
            state.output_dir = original_output

    def test_load_saved_messages_on_init(self, tmp_path):
        """JSON pre-existant → textes charges au demarrage."""
        import json

        os.makedirs(str(tmp_path), exist_ok=True)
        json_path = os.path.join(str(tmp_path), "messages.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"pre_decroche": "Texte persiste", "attente": "Attente perso"}, f)

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            from telephonia.config import get_default_messages

            state.messages = get_default_messages(music_path=state.music_path)
            state.load_saved_messages()

            pre = state.get_message("pre_decroche")
            assert pre.text == "Texte persiste"
            attente = state.get_message("attente")
            assert attente.text == "Attente perso"
        finally:
            state.output_dir = original_output

    def test_load_saved_messages_json_corrupted(self, tmp_path):
        """JSON invalide → messages par defaut, pas d'exception."""
        os.makedirs(str(tmp_path), exist_ok=True)
        json_path = os.path.join(str(tmp_path), "messages.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write("{invalid json content!!!")

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            from telephonia.config import get_default_messages

            state.messages = get_default_messages(music_path=state.music_path)
            original_text = state.get_message("pre_decroche").text

            state.load_saved_messages()

            assert state.get_message("pre_decroche").text == original_text
        finally:
            state.output_dir = original_output

    def test_load_saved_messages_unknown_key(self, tmp_path):
        """Cle inconnue → ignoree, autres messages charges normalement."""
        import json

        os.makedirs(str(tmp_path), exist_ok=True)
        json_path = os.path.join(str(tmp_path), "messages.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {"pre_decroche": "Texte connu", "cle_fantome": "Ignoree"},
                f,
            )

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            from telephonia.config import get_default_messages

            state.messages = get_default_messages(music_path=state.music_path)
            state.load_saved_messages()

            assert state.get_message("pre_decroche").text == "Texte connu"
            # La cle inconnue n'a pas cree de message
            assert state.get_message("cle_fantome") is None
        finally:
            state.output_dir = original_output


class TestVoices:
    """Tests pour GET /api/voices et PUT /api/voice."""

    @patch("telephonia.web.api.create_tts_provider")
    def test_get_voices(self, mock_create_provider, client):
        """GET /api/voices retourne la liste des voix."""
        mock_provider = MagicMock()
        mock_provider.list_voices.return_value = [
            {"id": "voice1", "name": "Voix 1"},
            {"id": "voice2", "name": "Voix 2"},
        ]
        mock_provider.voice = "voice1"
        mock_create_provider.return_value = mock_provider
        # Pas de client attr → provider edge
        del mock_provider.client

        response = client.get("/api/voices")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "edge"
        assert len(data["voices"]) == 2
        assert data["current"] == "voice1"

    def test_set_voice(self, client):
        """PUT /api/voice met a jour state.voice_id."""
        original = state.voice_id
        try:
            response = client.put("/api/voice", json={"voice_id": "fr-FR-HenriNeural"})
            assert response.status_code == 200
            assert response.json()["voice_id"] == "fr-FR-HenriNeural"
            assert state.voice_id == "fr-FR-HenriNeural"
        finally:
            state.voice_id = original

    @patch("telephonia.web.api.create_tts_provider")
    def test_generate_uses_selected_voice(self, mock_create_provider, client, tmp_path):
        """POST /api/generate passe la voix selectionnee a create_tts_provider."""
        import io

        from pydub.generators import Sine

        tone = Sine(440).to_audio_segment(duration=2000)
        buffer = io.BytesIO()
        tone.export(buffer, format="mp3")
        fake_audio = buffer.getvalue()

        mock_provider = MagicMock()
        mock_provider.synthesize_batch.side_effect = lambda texts: [fake_audio] * len(texts)
        mock_provider.voice_format = "mp3"
        mock_create_provider.return_value = mock_provider

        original_output = state.output_dir
        original_voice = state.voice_id
        state.output_dir = str(tmp_path)
        state.voice_id = "fr-FR-HenriNeural"
        try:
            client.post("/api/generate")
            mock_create_provider.assert_called_once_with(voice="fr-FR-HenriNeural")
        finally:
            state.output_dir = original_output
            state.voice_id = original_voice


class TestPrefix:
    """Tests pour GET /api/prefix et PUT /api/prefix."""

    def test_get_prefix_default_empty(self, client):
        """GET /api/prefix retourne une chaine vide par defaut."""
        response = client.get("/api/prefix")
        assert response.status_code == 200
        assert response.json() == {"prefix": ""}

    def test_set_prefix_valid(self, client):
        """PUT /api/prefix avec valeur valide → 200 + state mis a jour."""
        response = client.put("/api/prefix", json={"prefix": "mairie_cantine"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["prefix"] == "mairie_cantine"
        assert state.prefix == "mairie_cantine"

    def test_set_prefix_empty_clears(self, client):
        """PUT /api/prefix avec chaine vide → 200, state vide."""
        state.prefix = "ancien"
        response = client.put("/api/prefix", json={"prefix": ""})
        assert response.status_code == 200
        assert response.json()["prefix"] == ""
        assert state.prefix == ""

    def test_set_prefix_trims_whitespace(self, client):
        """PUT /api/prefix trime les espaces."""
        response = client.put("/api/prefix", json={"prefix": "  demo  "})
        assert response.status_code == 200
        assert response.json()["prefix"] == "demo"

    def test_set_prefix_invalid_chars(self, client):
        """PUT /api/prefix avec caracteres interdits → 400."""
        response = client.put("/api/prefix", json={"prefix": "mairie cantine!"})
        assert response.status_code == 400
        assert "Prefixe invalide" in response.json()["detail"]

    def test_set_prefix_too_long(self, client):
        """PUT /api/prefix avec > 64 caracteres → 400."""
        response = client.put("/api/prefix", json={"prefix": "a" * 65})
        assert response.status_code == 400

    def test_set_prefix_persists_in_json(self, client, tmp_path):
        """PUT /api/prefix → prefixe ecrit dans messages.json sous la cle _prefix."""
        import json

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            response = client.put("/api/prefix", json={"prefix": "mairie"})
            assert response.status_code == 200

            json_path = os.path.join(str(tmp_path), "messages.json")
            assert os.path.exists(json_path)
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["_prefix"] == "mairie"
        finally:
            state.output_dir = original_output

    def test_load_prefix_from_json(self, tmp_path):
        """JSON contenant _prefix → state.prefix charge au demarrage."""
        import json

        os.makedirs(str(tmp_path), exist_ok=True)
        json_path = os.path.join(str(tmp_path), "messages.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"_prefix": "persiste"}, f)

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            from telephonia.config import get_default_messages

            state.messages = get_default_messages(music_path=state.music_path)
            state.prefix = ""
            state.load_saved_messages()
            assert state.prefix == "persiste"
        finally:
            state.output_dir = original_output
            state.prefix = ""

    def test_load_prefix_invalid_ignored(self, tmp_path):
        """JSON contenant _prefix invalide → prefixe ignore (reste vide)."""
        import json

        os.makedirs(str(tmp_path), exist_ok=True)
        json_path = os.path.join(str(tmp_path), "messages.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"_prefix": "mechant prefixe !"}, f)

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            from telephonia.config import get_default_messages

            state.messages = get_default_messages(music_path=state.music_path)
            state.prefix = ""
            state.load_saved_messages()
            assert state.prefix == ""
        finally:
            state.output_dir = original_output

    @patch("telephonia.web.api.create_tts_provider")
    def test_generate_uses_prefix_in_filenames(self, mock_create_provider, client, tmp_path):
        """POST /api/generate avec prefixe → fichiers WAV prefixes sur le disque."""
        tone = Sine(440).to_audio_segment(duration=2000)
        buffer = io.BytesIO()
        tone.export(buffer, format="mp3")
        fake_audio = buffer.getvalue()

        mock_provider = MagicMock()
        mock_provider.synthesize_batch.side_effect = lambda texts: [fake_audio] * len(texts)
        mock_provider.voice_format = "mp3"
        mock_create_provider.return_value = mock_provider

        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        state.prefix = "mairie_cantine"
        try:
            response = client.post("/api/generate")
            assert response.status_code == 200

            for name in ("pre_decroche", "attente", "repondeur"):
                expected = os.path.join(str(tmp_path), f"mairie_cantine_{name}.wav")
                assert os.path.exists(expected), f"manquant : {expected}"
                # Sans prefixe → ne doit PAS exister
                assert not os.path.exists(os.path.join(str(tmp_path), f"{name}.wav"))
        finally:
            state.output_dir = original_output

    def test_get_audio_uses_prefix(self, client, tmp_path):
        """GET /api/audio/{name} sert le fichier prefixe et le telecharge sous ce nom."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        state.prefix = "demo"
        try:
            tone = Sine(440).to_audio_segment(duration=500)
            wav_path = os.path.join(str(tmp_path), "demo_pre_decroche.wav")
            tone.export(wav_path, format="wav")

            response = client.get("/api/audio/pre_decroche")
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"
            # Le Content-Disposition doit proposer le nom prefixe
            disp = response.headers.get("content-disposition", "")
            assert "demo_pre_decroche.wav" in disp
        finally:
            state.output_dir = original_output


class TestShutdown:
    """Tests pour POST /api/shutdown."""

    @patch("telephonia.web.api.os.kill")
    def test_shutdown_sends_sigint(self, mock_kill, client):
        """POST /api/shutdown → envoie SIGINT au process."""
        response = client.post("/api/shutdown")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_kill.assert_called_once()
        args = mock_kill.call_args[0]
        assert args[1] == signal.SIGINT


class TestGetAudio:
    """Tests pour GET /api/audio/{name}."""

    def test_get_audio_not_found(self, client):
        response = client.get("/api/audio/inexistant")
        assert response.status_code == 404

    def test_get_audio_existing(self, client, tmp_path):
        tone = Sine(440).to_audio_segment(duration=1000)
        wav_path = os.path.join(state.output_dir, "pre_decroche.wav")
        os.makedirs(state.output_dir, exist_ok=True)
        tone.export(wav_path, format="wav")

        try:
            response = client.get("/api/audio/pre_decroche")
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)


class TestGetAudioSecurity:
    """Tests de securite pour GET /api/audio/{name}."""

    def test_get_audio_path_traversal(self, client):
        """Tentative de path traversal → 400."""
        response = client.get("/api/audio/../../etc/passwd")
        assert response.status_code in (400, 404, 422)

    def test_get_audio_invalid_name_special_chars(self, client):
        """Nom avec caracteres speciaux → 400."""
        response = client.get("/api/audio/test%00file")
        assert response.status_code in (400, 404, 422)

    def test_get_audio_valid_name_format(self, client):
        """Nom valide mais fichier absent → 404 (pas 400)."""
        response = client.get("/api/audio/nom_valide-123")
        assert response.status_code == 404


class TestGenerateMessages:
    """Tests pour POST /api/generate."""

    @patch("telephonia.web.api.create_tts_provider")
    def test_generate_messages(self, mock_create_provider, client, tmp_path):
        # Creer un faux audio de retour
        tone = Sine(440).to_audio_segment(duration=2000)
        buffer = io.BytesIO()
        tone.export(buffer, format="mp3")
        fake_audio = buffer.getvalue()

        mock_provider = MagicMock()
        mock_provider.synthesize.return_value = fake_audio
        mock_provider.synthesize_batch.side_effect = lambda texts: [fake_audio] * len(texts)
        mock_provider.voice_format = "mp3"
        mock_create_provider.return_value = mock_provider

        # Utiliser un dossier temporaire pour la sortie
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            response = client.post("/api/generate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert len(data["results"]) == 3
            mock_provider.synthesize_batch.assert_called_once()
        finally:
            state.output_dir = original_output

    @patch("telephonia.web.api.create_tts_provider")
    def test_generate_tts_failure(self, mock_create_provider, client):
        """POST /api/generate avec TTS en erreur → 500 JSON."""
        from telephonia.tts import TTSError

        mock_provider = MagicMock()
        mock_provider.synthesize_batch.side_effect = TTSError("Service TTS indisponible")
        mock_provider.voice_format = "mp3"
        mock_create_provider.return_value = mock_provider

        response = client.post("/api/generate")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestAudioUpload:
    """Tests pour POST /api/audio/{name}/upload."""

    def test_upload_audio_mp3(self, client, tmp_path):
        """Upload MP3 → WAV telephonie (16kHz, mono, 16bit)."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            tone = Sine(440).to_audio_segment(duration=1000)
            buffer = io.BytesIO()
            tone.export(buffer, format="mp3")
            mp3_content = buffer.getvalue()

            response = client.post(
                "/api/audio/pre_decroche/upload",
                files={"file": ("test.mp3", mp3_content, "audio/mpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["name"] == "pre_decroche"

            wav_path = os.path.join(str(tmp_path), "pre_decroche.wav")
            assert os.path.exists(wav_path)

            from pydub import AudioSegment

            result = AudioSegment.from_wav(wav_path)
            assert result.frame_rate == 16000
            assert result.channels == 1
            assert result.sample_width == 2
        finally:
            state.output_dir = original_output

    def test_upload_audio_wav(self, client, tmp_path):
        """Upload WAV source → WAV telephonie avec bonnes specs."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            tone = Sine(880).to_audio_segment(duration=500).set_frame_rate(44100).set_channels(2)
            buffer = io.BytesIO()
            tone.export(buffer, format="wav")
            wav_content = buffer.getvalue()

            response = client.post(
                "/api/audio/attente/upload",
                files={"file": ("source.wav", wav_content, "audio/wav")},
            )
            assert response.status_code == 200

            wav_path = os.path.join(str(tmp_path), "attente.wav")
            assert os.path.exists(wav_path)

            from pydub import AudioSegment

            result = AudioSegment.from_wav(wav_path)
            assert result.frame_rate == 16000
            assert result.channels == 1
            assert result.sample_width == 2
        finally:
            state.output_dir = original_output

    def test_upload_audio_invalid_name(self, client):
        """Nom avec caracteres speciaux → 400."""
        response = client.post(
            "/api/audio/inv@lid!name/upload",
            files={"file": ("test.mp3", b"\x00" * 100, "audio/mpeg")},
        )
        assert response.status_code == 400

    def test_upload_audio_invalid_format(self, client):
        """Fichier .txt → 400."""
        response = client.post(
            "/api/audio/pre_decroche/upload",
            files={"file": ("notes.txt", b"Hello world", "text/plain")},
        )
        assert response.status_code == 400
        assert "Format" in response.json()["detail"]

    def test_upload_audio_unknown_message(self, client):
        """Message inexistant → 404."""
        tone = Sine(440).to_audio_segment(duration=500)
        buffer = io.BytesIO()
        tone.export(buffer, format="mp3")

        response = client.post(
            "/api/audio/message_fantome/upload",
            files={"file": ("test.mp3", buffer.getvalue(), "audio/mpeg")},
        )
        assert response.status_code == 404

    def test_upload_audio_with_music_mixes(self, client, tmp_path):
        """Upload MP3 sur message has_music + musique dispo → mixe la musique."""
        original_output = state.output_dir
        original_music = state.music_path

        # Creer un fichier musique de fond
        music = Sine(330).to_audio_segment(duration=5000)
        music_path = os.path.join(str(tmp_path), "musique.mp3")
        music.export(music_path, format="mp3")
        state.music_path = music_path
        state.output_dir = str(tmp_path)

        try:
            # pre_decroche a has_music=True
            voice = Sine(440).to_audio_segment(duration=1000)
            buf = io.BytesIO()
            voice.export(buf, format="mp3")

            response = client.post(
                "/api/audio/pre_decroche/upload",
                files={"file": ("voix.mp3", buf.getvalue(), "audio/mpeg")},
            )
            assert response.status_code == 200

            from pydub import AudioSegment

            wav_path = os.path.join(str(tmp_path), "pre_decroche.wav")
            result = AudioSegment.from_wav(wav_path)
            # Le mix ajoute intro + outro, donc le WAV doit etre plus long
            assert len(result) > 1000
            assert result.frame_rate == 16000
        finally:
            state.output_dir = original_output
            state.music_path = original_music

    @patch("telephonia.web.api.convert_g729_to_wav")
    def test_upload_g729_sets_flag(self, mock_convert, client, tmp_path):
        """Upload G.729 → flag imported_g729 dans GET /api/messages."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            # Simuler la conversion : creer un fichier WAV factice
            def fake_convert(input_path, output_path):
                tone = Sine(440).to_audio_segment(duration=500)
                tone.export(output_path, format="wav")
                return output_path

            mock_convert.side_effect = fake_convert

            response = client.post(
                "/api/audio/pre_decroche/upload",
                files={"file": ("old.g729", b"\x00" * 100, "audio/octet-stream")},
            )
            assert response.status_code == 200

            # Verifier le flag dans GET /api/messages
            msgs = client.get("/api/messages").json()
            pre = next(m for m in msgs if m["name"] == "pre_decroche")
            assert pre["imported_g729"] is True

            # Les autres messages ne sont pas marques
            attente = next(m for m in msgs if m["name"] == "attente")
            assert attente["imported_g729"] is False
        finally:
            state.output_dir = original_output

    def test_upload_mp3_clears_g729_flag(self, client, tmp_path):
        """Upload MP3 apres G.729 → flag imported_g729 efface."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        state.imported_g729.add("pre_decroche")
        try:
            tone = Sine(440).to_audio_segment(duration=500)
            buf = io.BytesIO()
            tone.export(buf, format="mp3")

            response = client.post(
                "/api/audio/pre_decroche/upload",
                files={"file": ("voix.mp3", buf.getvalue(), "audio/mpeg")},
            )
            assert response.status_code == 200
            assert "pre_decroche" not in state.imported_g729
        finally:
            state.output_dir = original_output


class TestDeleteAudio:
    """Tests pour DELETE /api/audio/{name}."""

    def test_delete_audio_existing(self, client, tmp_path):
        """DELETE audio existant → supprime le fichier."""
        original_output = state.output_dir
        state.output_dir = str(tmp_path)
        try:
            tone = Sine(440).to_audio_segment(duration=500)
            wav_path = os.path.join(str(tmp_path), "pre_decroche.wav")
            tone.export(wav_path, format="wav")
            assert os.path.exists(wav_path)

            response = client.delete("/api/audio/pre_decroche")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            assert not os.path.exists(wav_path)
        finally:
            state.output_dir = original_output

    def test_delete_audio_not_found(self, client):
        """DELETE audio inexistant → 404."""
        response = client.delete("/api/audio/inexistant")
        assert response.status_code == 404

    def test_delete_audio_invalid_name(self, client):
        """DELETE nom invalide → 400."""
        response = client.delete("/api/audio/inv@lid!")
        assert response.status_code == 400


class TestMusicUpload:
    """Tests pour GET/POST/DELETE /api/music."""

    def test_get_music_status(self, client):
        """GET /api/music retourne le statut."""
        response = client.get("/api/music")
        assert response.status_code == 200
        data = response.json()
        assert "has_music" in data

    def test_upload_mp3(self, client, tmp_path):
        """POST /api/music avec un fichier MP3 valide."""
        original_music = state.music_path
        with patch("telephonia.web.api.get_music_upload_dir", return_value=str(tmp_path)):
            mp3_content = b"\xff\xfb\x90\x00" + b"\x00" * 1000
            response = client.post(
                "/api/music",
                files={"file": ("test.mp3", mp3_content, "audio/mpeg")},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            assert os.path.exists(os.path.join(str(tmp_path), "musique_fond.mp3"))
        state.music_path = original_music

    def test_upload_rejects_non_mp3(self, client):
        """POST /api/music avec un fichier non-MP3 → 400."""
        response = client.post(
            "/api/music",
            files={"file": ("test.wav", b"\x00" * 100, "audio/wav")},
        )
        assert response.status_code == 400
        assert "MP3" in response.json()["detail"]

    def test_upload_rejects_too_large(self, client):
        """POST /api/music avec un fichier trop gros → 400."""
        big_content = b"\xff\xfb\x90\x00" + b"\x00" * (21 * 1024 * 1024)
        response = client.post(
            "/api/music",
            files={"file": ("big.mp3", big_content, "audio/mpeg")},
        )
        assert response.status_code == 400
        assert "volumineux" in response.json()["detail"]

    def test_delete_music(self, client, tmp_path):
        """DELETE /api/music supprime le fichier."""
        music_file = os.path.join(str(tmp_path), "musique_fond.mp3")
        with open(music_file, "wb") as f:
            f.write(b"\xff\xfb\x90\x00")

        original_music = state.music_path
        with patch("telephonia.web.api.get_music_upload_dir", return_value=str(tmp_path)):
            with patch("telephonia.web.api.get_music_path", return_value=None):
                response = client.delete("/api/music")
                assert response.status_code == 200
                assert not os.path.exists(music_file)
                assert response.json()["has_music"] is False
        state.music_path = original_music

    def test_delete_music_no_file(self, client, tmp_path):
        """DELETE /api/music sans fichier → OK quand meme."""
        original_music = state.music_path
        with patch("telephonia.web.api.get_music_upload_dir", return_value=str(tmp_path)):
            with patch("telephonia.web.api.get_music_path", return_value=None):
                response = client.delete("/api/music")
                assert response.status_code == 200
        state.music_path = original_music
