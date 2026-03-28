"""Tests pour le module converter."""

import os
import wave
from unittest.mock import patch

import pytest

from telephonia.converter import check_ffmpeg, convert_batch, convert_g729_to_wav


def _make_fake_g729(path: str) -> str:
    """Cree un faux fichier G.729 (silence encode en WAV pour le test)."""
    # On cree un vrai WAV minimal que ffmpeg peut lire,
    # renomme en .g729 pour tester le pipeline
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        # 1 seconde de silence
        wf.writeframes(b"\x00\x00" * 8000)
    return path


class TestCheckFfmpeg:
    """Tests pour check_ffmpeg."""

    def test_ffmpeg_found(self):
        path = check_ffmpeg()
        assert path is not None
        assert "ffmpeg" in path

    @patch("telephonia.converter.shutil.which", return_value=None)
    def test_ffmpeg_not_found(self, mock_which):
        with pytest.raises(SystemExit):
            check_ffmpeg()


class TestConvertG729ToWav:
    """Tests pour convert_g729_to_wav."""

    def test_convert_success(self, tmp_path):
        input_path = str(tmp_path / "test.g729")
        output_path = str(tmp_path / "test.wav")
        _make_fake_g729(input_path)

        result = convert_g729_to_wav(input_path, output_path)

        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_output_is_16khz_mono_16bit(self, tmp_path):
        input_path = str(tmp_path / "test.g729")
        output_path = str(tmp_path / "test.wav")
        _make_fake_g729(input_path)

        convert_g729_to_wav(input_path, output_path)

        with wave.open(output_path, "r") as wf:
            assert wf.getframerate() == 16000
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_g729_to_wav(str(tmp_path / "inexistant.g729"), str(tmp_path / "out.wav"))


class TestConvertBatch:
    """Tests pour convert_batch."""

    def test_batch_converts_g729_files(self, tmp_path):
        input_dir = str(tmp_path / "input")
        output_dir = str(tmp_path / "output")
        os.makedirs(input_dir)

        _make_fake_g729(os.path.join(input_dir, "msg1.g729"))
        _make_fake_g729(os.path.join(input_dir, "msg2.g729"))
        # Fichier non-G.729, doit etre ignore
        with open(os.path.join(input_dir, "readme.txt"), "w") as f:
            f.write("ignore moi")

        results = convert_batch(input_dir, output_dir)

        assert len(results) == 2
        assert all("OK" in r["status"] for r in results)
        assert os.path.exists(os.path.join(output_dir, "msg1.wav"))
        assert os.path.exists(os.path.join(output_dir, "msg2.wav"))

    def test_batch_empty_directory(self, tmp_path):
        input_dir = str(tmp_path / "empty")
        output_dir = str(tmp_path / "output")
        os.makedirs(input_dir)

        results = convert_batch(input_dir, output_dir)

        assert len(results) == 0

    def test_batch_creates_output_dir(self, tmp_path):
        input_dir = str(tmp_path / "input")
        output_dir = str(tmp_path / "new_output")
        os.makedirs(input_dir)
        _make_fake_g729(os.path.join(input_dir, "test.g729"))

        convert_batch(input_dir, output_dir)

        assert os.path.isdir(output_dir)
