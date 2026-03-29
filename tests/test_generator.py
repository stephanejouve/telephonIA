"""Tests pour le module generator."""

import io
import os
from unittest.mock import MagicMock, patch

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from telephonia.config import SVIMessage
from telephonia.generator import GenerationError, SVIGenerator, get_api_key
from telephonia.tts import NetworkError, TTSError


@pytest.fixture
def fake_voice_bytes():
    """Audio synthetique pour simuler la sortie TTS (WAV)."""
    tone = Sine(440).to_audio_segment(duration=2000)
    buffer = io.BytesIO()
    tone.export(buffer, format="wav")
    return buffer.getvalue()


@pytest.fixture
def mock_tts(fake_voice_bytes):
    """Client TTS mocke."""
    tts = MagicMock()
    tts.synthesize.return_value = fake_voice_bytes
    tts.synthesize_batch.side_effect = lambda texts: [fake_voice_bytes] * len(texts)
    return tts


@pytest.fixture
def music_file(tmp_path):
    """Fichier musique temporaire (WAV)."""
    tone = Sine(220).to_audio_segment(duration=3000)
    path = str(tmp_path / "music.wav")
    tone.export(path, format="wav")
    return path


class TestSVIGenerator:
    """Tests pour l'orchestrateur SVIGenerator."""

    def test_generate_message_without_music(self, mock_tts, tmp_path):
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        message = SVIMessage(name="test", text="Bonjour", target_duration=5)

        result = generator.generate_message(message)

        assert result["name"] == "test"
        assert os.path.exists(result["wav"])
        assert result["wav"].endswith(".wav")
        mock_tts.synthesize.assert_called_once_with("Bonjour")

    def test_generate_message_with_music(self, mock_tts, tmp_path, music_file):
        generator = SVIGenerator(
            tts=mock_tts, music_path=music_file, output_dir=str(tmp_path), voice_format="wav"
        )
        message = SVIMessage(
            name="attente",
            text="Veuillez patienter",
            target_duration=10,
            background_music=music_file,
            music_volume_db=-15.0,
        )

        result = generator.generate_message(message)

        assert result["name"] == "attente"
        assert os.path.exists(result["wav"])

    def test_generate_message_creates_output_dir(self, mock_tts, tmp_path):
        output_dir = str(tmp_path / "new_output")
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=output_dir, voice_format="wav"
        )
        message = SVIMessage(name="test", text="Bonjour", target_duration=5)

        generator.generate_message(message)

        assert os.path.isdir(output_dir)

    def test_generate_all_default_messages(self, mock_tts, tmp_path):
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )

        results = generator.generate_all()

        assert len(results) == 3
        assert results[0]["name"] == "pre_decroche"
        assert results[1]["name"] == "attente"
        assert results[2]["name"] == "repondeur"
        mock_tts.synthesize_batch.assert_called_once()

    def test_generate_all_custom_messages(self, mock_tts, tmp_path):
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        messages = [
            SVIMessage(name="msg1", text="Premier", target_duration=5),
            SVIMessage(name="msg2", text="Deuxieme", target_duration=10),
        ]

        results = generator.generate_all(messages=messages)

        assert len(results) == 2
        assert results[0]["name"] == "msg1"
        assert results[1]["name"] == "msg2"

    def test_generate_all_produces_files(self, mock_tts, tmp_path):
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        messages = [SVIMessage(name="test", text="Bonjour", target_duration=5)]

        results = generator.generate_all(messages=messages)

        for result in results:
            assert os.path.exists(result["wav"])
            assert os.path.getsize(result["wav"]) > 0

    def test_wav_is_telephony_format(self, mock_tts, tmp_path):
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        message = SVIMessage(name="test", text="Bonjour", target_duration=5)

        result = generator.generate_message(message)

        wav = AudioSegment.from_file(result["wav"], format="wav")
        assert wav.frame_rate == 16000
        assert wav.channels == 1
        assert wav.sample_width == 2

    def test_generate_all_uses_batch(self, fake_voice_bytes, tmp_path):
        """generate_all() utilise synthesize_batch (pas synthesize)."""
        tts = MagicMock()
        tts.synthesize_batch.return_value = [
            fake_voice_bytes,
            fake_voice_bytes,
            fake_voice_bytes,
        ]
        generator = SVIGenerator(
            tts=tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )

        results = generator.generate_all()

        tts.synthesize_batch.assert_called_once()
        tts.synthesize.assert_not_called()
        assert len(results) == 3

    def test_generate_all_partial_failure(self, fake_voice_bytes, tmp_path):
        """Message 2 echoue en TTS → messages 1 et 3 generes, message 2 erreur."""
        tts = MagicMock()
        tts.synthesize_batch.return_value = [
            fake_voice_bytes,
            TTSError("Service indisponible"),
            fake_voice_bytes,
        ]
        generator = SVIGenerator(
            tts=tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        messages = [
            SVIMessage(name="msg1", text="Premier", target_duration=5),
            SVIMessage(name="msg2", text="Deuxieme", target_duration=5),
            SVIMessage(name="msg3", text="Troisieme", target_duration=5),
        ]

        results = generator.generate_all(messages=messages)

        assert len(results) == 3
        # Message 1 OK
        assert "wav" in results[0]
        assert results[0]["name"] == "msg1"
        # Message 2 erreur
        assert "error" in results[1]
        assert results[1]["name"] == "msg2"
        assert "Service indisponible" in results[1]["error"]
        # Message 3 OK
        assert "wav" in results[2]
        assert results[2]["name"] == "msg3"

    def test_generate_message_tts_error(self, tmp_path):
        """TTSError dans le TTS → GenerationError."""
        tts = MagicMock()
        tts.synthesize.side_effect = TTSError("Service indisponible")
        generator = SVIGenerator(
            tts=tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        message = SVIMessage(name="test", text="Bonjour", target_duration=5)

        with pytest.raises(GenerationError, match="Synthese vocale echouee"):
            generator.generate_message(message)

    def test_generate_message_network_error(self, tmp_path):
        """NetworkError (connexion) dans le TTS → GenerationError."""
        tts = MagicMock()
        tts.synthesize.side_effect = NetworkError("Connexion impossible")
        generator = SVIGenerator(
            tts=tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        message = SVIMessage(name="test", text="Bonjour", target_duration=5)

        with pytest.raises(GenerationError, match="Synthese vocale echouee"):
            generator.generate_message(message)

    def test_generate_message_missing_music(self, mock_tts, tmp_path):
        """Musique de fond introuvable → GenerationError."""
        generator = SVIGenerator(
            tts=mock_tts,
            music_path="/inexistant/music.mp3",
            output_dir=str(tmp_path),
            voice_format="wav",
        )
        message = SVIMessage(
            name="test",
            text="Bonjour",
            target_duration=5,
            background_music="/inexistant/music.mp3",
        )

        with pytest.raises(GenerationError, match="Mixage echoue"):
            generator.generate_message(message)


class TestMusicRefresh:
    """Tests pour _refresh_music qui utilise self.music_path."""

    def test_refresh_music_uses_constructor_path(self, mock_tts, tmp_path, music_file):
        """_refresh_music utilise self.music_path, pas get_music_path()."""
        generator = SVIGenerator(
            tts=mock_tts, music_path=music_file, output_dir=str(tmp_path), voice_format="wav"
        )
        messages = [
            SVIMessage(
                name="attente",
                text="Veuillez patienter",
                target_duration=10,
                background_music=None,
            ),
        ]

        results = generator.generate_all(messages=messages)

        assert len(results) == 1
        assert "wav" in results[0]
        assert os.path.exists(results[0]["wav"])
        assert messages[0].background_music == music_file

    def test_refresh_music_none_no_mix(self, mock_tts, tmp_path):
        """music_path=None → voix seule, pas de mixage."""
        generator = SVIGenerator(
            tts=mock_tts, music_path=None, output_dir=str(tmp_path), voice_format="wav"
        )
        messages = [
            SVIMessage(
                name="attente",
                text="Veuillez patienter",
                target_duration=10,
                background_music=None,
            ),
        ]

        results = generator.generate_all(messages=messages)

        assert len(results) == 1
        assert "wav" in results[0]
        assert messages[0].background_music is None


class TestGetApiKey:
    """Tests pour get_api_key."""

    @patch("telephonia.generator.keyring.get_password")
    def testget_api_key_success(self, mock_get):
        mock_get.return_value = "my-secret-key"
        key = get_api_key()
        assert key == "my-secret-key"
        mock_get.assert_called_once_with("elevenlabs_api_key", "telephonia")

    @patch("telephonia.generator.keyring.get_password")
    def testget_api_key_not_found(self, mock_get):
        mock_get.return_value = None
        with pytest.raises(SystemExit):
            get_api_key()
