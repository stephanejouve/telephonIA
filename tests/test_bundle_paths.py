"""Tests pour les fonctions de chemins dev/bundle PyInstaller."""

import os
from unittest.mock import patch

from telephonia.paths import get_ffmpeg_path, get_static_dir


class TestGetStaticPath:
    """Tests pour get_static_dir."""

    def test_dev_context(self):
        """Hors contexte frozen, pointe vers web/static."""
        result = get_static_dir()
        assert result.endswith("static")
        assert "web" in result

    @patch("telephonia.paths.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, utilise _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        result = get_static_dir()
        assert result == os.path.join("/tmp/pyinstaller_bundle", "static")


class TestGetFfmpegPath:
    """Tests pour get_ffmpeg_path."""

    def test_dev_context(self):
        """Hors contexte frozen, retourne 'ffmpeg' (systeme)."""
        result = get_ffmpeg_path()
        assert result == "ffmpeg"

    @patch("telephonia.paths.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, retourne ffmpeg.exe dans _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        result = get_ffmpeg_path()
        assert result == os.path.join("/tmp/pyinstaller_bundle", "ffmpeg.exe")
