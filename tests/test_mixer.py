"""Tests pour le module mixer."""

import io
import os
import shutil

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

from telephonia.mixer import export_audio, export_telephony, mix_voice_with_music

has_ffmpeg = shutil.which("ffmpeg") is not None
requires_ffmpeg = pytest.mark.skipif(not has_ffmpeg, reason="ffmpeg non installe")


@pytest.fixture
def voice_audio_bytes():
    """Genere un audio voix synthetique (sine wave) en bytes WAV."""
    tone = Sine(440).to_audio_segment(duration=3000)  # 3 secondes, 440 Hz
    buffer = io.BytesIO()
    tone.export(buffer, format="wav")
    return buffer.getvalue()


@pytest.fixture
def music_file(tmp_path):
    """Cree un fichier musique temporaire (sine wave WAV)."""
    tone = Sine(220).to_audio_segment(duration=5000)  # 5 secondes, 220 Hz
    path = str(tmp_path / "music.wav")
    tone.export(path, format="wav")
    return path


@pytest.fixture
def short_music_file(tmp_path):
    """Cree un fichier musique court (pour tester le bouclage)."""
    tone = Sine(220).to_audio_segment(duration=1000)  # 1 seconde
    path = str(tmp_path / "short_music.wav")
    tone.export(path, format="wav")
    return path


@pytest.fixture
def sample_audio():
    """Cree un AudioSegment de test."""
    return Sine(440).to_audio_segment(duration=2000)


class TestMixVoiceWithMusic:
    """Tests pour mix_voice_with_music."""

    def test_mix_produces_audio_segment(self, voice_audio_bytes, music_file):
        result = mix_voice_with_music(voice_audio_bytes, music_file, voice_format="wav")
        assert isinstance(result, AudioSegment)

    def test_mix_duration_matches_voice(self, voice_audio_bytes, music_file):
        result = mix_voice_with_music(voice_audio_bytes, music_file, voice_format="wav")
        voice = AudioSegment.from_file(io.BytesIO(voice_audio_bytes), format="wav")
        # La duree du mix doit correspondre a la voix (tolerance de 50ms)
        assert abs(len(result) - len(voice)) < 50

    def test_mix_with_short_music_loops(self, voice_audio_bytes, short_music_file):
        result = mix_voice_with_music(voice_audio_bytes, short_music_file, voice_format="wav")
        assert isinstance(result, AudioSegment)
        # Le mix doit avoir la duree de la voix meme si la musique est courte
        voice = AudioSegment.from_file(io.BytesIO(voice_audio_bytes), format="wav")
        assert abs(len(result) - len(voice)) < 50

    def test_mix_with_custom_volume(self, voice_audio_bytes, music_file):
        result = mix_voice_with_music(
            voice_audio_bytes, music_file, music_volume_db=-20.0, voice_format="wav"
        )
        assert isinstance(result, AudioSegment)

    def test_mix_with_custom_fades(self, voice_audio_bytes, music_file):
        result = mix_voice_with_music(
            voice_audio_bytes, music_file, fade_in_ms=500, fade_out_ms=500, voice_format="wav"
        )
        assert isinstance(result, AudioSegment)


class TestExportAudio:
    """Tests pour export_audio."""

    @requires_ffmpeg
    def test_export_mp3(self, sample_audio, tmp_path):
        output = str(tmp_path / "output.mp3")
        result = export_audio(sample_audio, output, format="mp3")
        assert result == output
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

    def test_export_wav(self, sample_audio, tmp_path):
        output = str(tmp_path / "output.wav")
        result = export_audio(sample_audio, output, format="wav")
        assert result == output
        assert os.path.exists(output)

    @requires_ffmpeg
    def test_export_custom_bitrate(self, sample_audio, tmp_path):
        output = str(tmp_path / "output.mp3")
        result = export_audio(sample_audio, output, format="mp3", bitrate="128k")
        assert os.path.exists(result)


class TestMixVoiceWithMusicErrors:
    """Tests d'erreur pour mix_voice_with_music."""

    def test_mix_music_file_missing(self, voice_audio_bytes):
        """Musique introuvable → FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="introuvable"):
            mix_voice_with_music(
                voice_audio_bytes, "/chemin/inexistant/musique.mp3", voice_format="wav"
            )


class TestExportTelephonyErrors:
    """Tests d'erreur pour export_telephony."""

    def test_export_permission_error(self, sample_audio):
        """Ecriture impossible → IOError."""
        with pytest.raises((IOError, OSError)):
            export_telephony(sample_audio, "/chemin/inexistant/output.wav")


class TestExportTelephony:
    """Tests pour export_telephony."""

    def test_export_telephony_format(self, sample_audio, tmp_path):
        output = str(tmp_path / "output.wav")
        result = export_telephony(sample_audio, output)
        assert result == output
        assert os.path.exists(output)

        # Verifier les proprietes du fichier telephonie
        telephony = AudioSegment.from_file(output, format="wav")
        assert telephony.frame_rate == 16000
        assert telephony.channels == 1
        assert telephony.sample_width == 2  # 16 bits

    def test_export_telephony_returns_path(self, sample_audio, tmp_path):
        output = str(tmp_path / "telephony.wav")
        result = export_telephony(sample_audio, output)
        assert result == output
