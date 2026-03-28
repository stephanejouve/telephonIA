"""Tests pour les fonctions de chemins dev/bundle PyInstaller."""

import os
from unittest.mock import patch

from telephonia.web.app import get_ffmpeg_path, get_static_path


class TestGetStaticPath:
    """Tests pour get_static_path."""

    def test_dev_context(self):
        """Hors contexte frozen, pointe vers web/static."""
        result = get_static_path()
        assert result.endswith("static")
        assert "web" in result

    @patch("telephonia.web.app.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, utilise _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        # getattr doit fonctionner sur le mock
        result = get_static_path()
        assert result == os.path.join("/tmp/pyinstaller_bundle", "static")


class TestGetFfmpegPath:
    """Tests pour get_ffmpeg_path."""

    def test_dev_context(self):
        """Hors contexte frozen, retourne 'ffmpeg' (systeme)."""
        result = get_ffmpeg_path()
        assert result == "ffmpeg"

    @patch("telephonia.web.app.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, retourne ffmpeg.exe dans _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        result = get_ffmpeg_path()
        assert result == os.path.join("/tmp/pyinstaller_bundle", "ffmpeg.exe")
