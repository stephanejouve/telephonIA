"""Tests pour le module generator."""

import io
import os
import shutil
from unittest.mock import MagicMock, patch

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from telephonia.config import SVIMessage
from telephonia.generator import SVIGenerator, _get_api_key

has_ffmpeg = shutil.which("ffmpeg") is not None
requires_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg non installe")


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
        assert os.path.exists(result["mp3"])
        assert os.path.exists(result["wav"])
        assert result["mp3"].endswith(".mp3")
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
        assert os.path.exists(result["mp3"])
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
        assert mock_tts.synthesize.call_count == 3

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
            assert os.path.exists(result["mp3"])
            assert os.path.exists(result["wav"])
            assert os.path.getsize(result["mp3"]) > 0
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


class TestGetApiKey:
    """Tests pour _get_api_key."""

    @patch("telephonia.generator.subprocess.run")
    def test_get_api_key_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="my-secret-key\n")
        key = _get_api_key()
        assert key == "my-secret-key"

    @patch("telephonia.generator.subprocess.run")
    def test_get_api_key_not_found(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "security")
        with pytest.raises(SystemExit):
            _get_api_key()
