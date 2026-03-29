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
