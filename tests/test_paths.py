"""Tests pour le module paths (resolution centralisee des chemins)."""

import os
from unittest.mock import patch

from telephonia.paths import (
    get_assets_dir,
    get_ffmpeg_path,
    get_music_path,
    get_output_dir,
    get_project_root,
    get_static_dir,
)


class TestGetProjectRoot:
    """Tests pour get_project_root."""

    def test_dev_context(self):
        """En dev, la racine contient src/."""
        root = get_project_root()
        assert os.path.isdir(os.path.join(root, "src"))

    @patch("telephonia.paths.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, retourne _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        assert get_project_root() == "/tmp/pyinstaller_bundle"


class TestGetMusicPath:
    """Tests pour get_music_path."""

    def test_music_absent(self):
        """Si le fichier n'existe pas, retourne None."""
        with patch("telephonia.paths.os.path.exists", return_value=False):
            assert get_music_path() is None

    def test_music_present(self):
        """Si le fichier existe, retourne le chemin."""
        with patch("telephonia.paths.os.path.exists", return_value=True):
            result = get_music_path()
            assert result is not None
            assert result.endswith("musique_fond.mp3")


class TestGetOutputDir:
    """Tests pour get_output_dir."""

    def test_output_path(self):
        """Le dossier output est sous la racine."""
        result = get_output_dir()
        assert result.endswith("output")
        assert os.path.dirname(result) == get_project_root()


class TestGetStaticDir:
    """Tests pour get_static_dir."""

    def test_dev_context(self):
        """En dev, pointe vers web/static."""
        result = get_static_dir()
        assert result.endswith("static")
        assert "web" in result

    @patch("telephonia.paths.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, utilise _MEIPASS/static."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        assert get_static_dir() == os.path.join("/tmp/pyinstaller_bundle", "static")


class TestGetFfmpegPath:
    """Tests pour get_ffmpeg_path."""

    def test_dev_context(self):
        """En dev, retourne 'ffmpeg' (systeme)."""
        assert get_ffmpeg_path() == "ffmpeg"

    @patch("telephonia.paths.sys")
    def test_frozen_context(self, mock_sys):
        """En contexte frozen, retourne ffmpeg.exe dans _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        assert get_ffmpeg_path() == os.path.join("/tmp/pyinstaller_bundle", "ffmpeg.exe")


class TestGetAssetsDir:
    """Tests pour get_assets_dir."""

    def test_assets_dir(self):
        """Le dossier assets est sous la racine."""
        result = get_assets_dir()
        assert result.endswith("assets")
        assert os.path.dirname(result) == get_project_root()
