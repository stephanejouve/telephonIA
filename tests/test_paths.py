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

    def test_output_path_dev(self):
        """En dev, le dossier output est sous la racine."""
        result = get_output_dir()
        assert result.endswith("output")
        assert os.path.dirname(result) == get_project_root()

    @patch("telephonia.paths.platform.system", return_value="Windows")
    @patch("telephonia.paths.sys")
    @patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"})
    def test_output_path_frozen_windows(self, mock_sys, _mock_platform):
        """En bundle Windows, output dans LOCALAPPDATA."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "C:\\tmp\\meipass"
        mock_sys.executable = "C:\\Program Files\\telephonIA\\telephonIA.exe"
        result = get_output_dir()
        assert "AppData" in result
        assert result.endswith(os.path.join("telephonIA", "output"))


class TestGetAssetsDir:
    """Tests pour get_assets_dir."""

    def test_assets_dir_dev(self):
        """En dev, le dossier assets est sous la racine."""
        result = get_assets_dir()
        assert result.endswith("assets")
        assert os.path.dirname(result) == get_project_root()

    @patch("telephonia.paths.sys")
    def test_assets_dir_frozen(self, mock_sys):
        """En bundle, assets est a cote de l'executable."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/meipass"
        mock_sys.executable = "/opt/telephonIA/telephonIA"
        result = get_assets_dir()
        assert result == os.path.join("/opt/telephonIA", "assets")


class TestGetMusicPathFrozen:
    """Tests pour get_music_path en contexte frozen Windows."""

    @patch("telephonia.paths.platform.system", return_value="Windows")
    @patch("telephonia.paths.sys")
    @patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"})
    def test_music_fallback_localappdata(self, mock_sys, _mock_platform):
        """En bundle Windows, fallback vers LOCALAPPDATA si absent a cote du exe."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "C:\\tmp\\meipass"
        mock_sys.executable = "C:\\Program Files\\telephonIA\\telephonIA.exe"

        def exists_side_effect(path):
            return "AppData" in path

        with patch("telephonia.paths.os.path.exists", side_effect=exists_side_effect):
            result = get_music_path()
        assert result is not None
        assert "AppData" in result
        assert result.endswith("musique_fond.mp3")


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
