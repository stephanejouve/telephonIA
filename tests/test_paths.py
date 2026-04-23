"""Tests pour le module paths (resolution centralisee des chemins)."""

import os
from unittest.mock import patch

from telephonia.paths import (
    _is_py2app,
    _is_pyinstaller,
    get_assets_dir,
    get_ffmpeg_path,
    get_ffprobe_path,
    get_music_path,
    get_music_upload_dir,
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


class TestGetMusicUploadDir:
    """Tests pour get_music_upload_dir."""

    def test_dev_context(self):
        """En dev, le dossier upload est sous assets/."""
        result = get_music_upload_dir()
        assert result.endswith("assets")

    @patch("telephonia.paths.platform.system", return_value="Windows")
    @patch("telephonia.paths.sys")
    @patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"})
    def test_frozen_windows(self, mock_sys, _mock_platform):
        """En bundle Windows, upload dans LOCALAPPDATA."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "C:\\tmp\\meipass"
        mock_sys.executable = "C:\\Program Files\\telephonIA\\telephonIA.exe"
        result = get_music_upload_dir()
        assert "AppData" in result
        assert result.endswith(os.path.join("telephonIA", "assets"))


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


class TestGetFfprobePath:
    """Tests pour get_ffprobe_path — binaire distinct de ffmpeg requis par pydub."""

    def test_dev_context(self):
        """En dev, retourne 'ffprobe' (systeme)."""
        assert get_ffprobe_path() == "ffprobe"

    @patch("telephonia.paths.sys")
    def test_pyinstaller_context(self, mock_sys):
        """En PyInstaller, retourne ffprobe.exe dans _MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        assert get_ffprobe_path() == os.path.join("/tmp/pyinstaller_bundle", "ffprobe.exe")


class TestDetectionHelpers:
    """Tests pour _is_pyinstaller et _is_py2app."""

    def test_dev_context(self):
        """En dev, les deux retournent False."""
        assert not _is_pyinstaller()
        assert not _is_py2app()

    @patch("telephonia.paths.sys")
    def test_pyinstaller(self, mock_sys):
        """PyInstaller met sys.frozen = True et sys._MEIPASS."""
        mock_sys.frozen = True
        mock_sys._MEIPASS = "/tmp/pyinstaller_bundle"
        assert _is_pyinstaller()
        assert not _is_py2app()

    @patch("telephonia.paths.sys")
    def test_py2app(self, mock_sys):
        """py2app met sys.frozen = 'macosx_app' mais pas sys._MEIPASS."""
        mock_sys.frozen = "macosx_app"
        # MagicMock auto-cree les attributs ; on supprime explicitement _MEIPASS
        # pour refleter le vrai environnement py2app qui n'a pas cet attribut
        # (propre au bootloader PyInstaller).
        del mock_sys._MEIPASS
        assert _is_py2app()
        assert not _is_pyinstaller()


class TestPy2appPaths:
    """Tests pour les chemins en contexte py2app (macOS .app)."""

    BUNDLE_DIR = "/Applications/telephonIA.app/Contents/Resources/python_backend"
    EXECUTABLE = BUNDLE_DIR + "/telephonia-web"
    DATA_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "telephonIA")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_project_root(self, mock_sys):
        """En py2app, retourne le dossier python_backend/ via RESOURCEPATH."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_project_root()
        assert result == self.BUNDLE_DIR

    @patch.dict(os.environ, {}, clear=True)
    @patch("telephonia.paths.sys")
    def test_get_project_root_fallback(self, mock_sys):
        """Sans RESOURCEPATH, fallback sur sys.executable."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        os.environ.pop("RESOURCEPATH", None)
        result = get_project_root()
        assert result == self.BUNDLE_DIR

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_assets_dir(self, mock_sys):
        """En py2app, assets est dans python_backend/assets."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_assets_dir()
        assert result == os.path.join(self.BUNDLE_DIR, "assets")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_music_upload_dir(self, mock_sys):
        """En py2app, uploads dans ~/Library/Application Support/telephonIA/assets."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_music_upload_dir()
        assert result == os.path.join(self.DATA_DIR, "assets")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_output_dir(self, mock_sys):
        """En py2app, output dans ~/Library/Application Support/telephonIA/output."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_output_dir()
        assert result == os.path.join(self.DATA_DIR, "output")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_static_dir(self, mock_sys):
        """En py2app, static dans python_backend/static."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_static_dir()
        assert result == os.path.join(self.BUNDLE_DIR, "static")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_ffmpeg_path(self, mock_sys):
        """En py2app, ffmpeg dans python_backend/ffmpeg."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_ffmpeg_path()
        assert result == os.path.join(self.BUNDLE_DIR, "ffmpeg")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_ffprobe_path(self, mock_sys):
        """En py2app, ffprobe dans python_backend/ffprobe (distinct de ffmpeg)."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        result = get_ffprobe_path()
        assert result == os.path.join(self.BUNDLE_DIR, "ffprobe")

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_music_path_upload(self, mock_sys):
        """En py2app, musique trouvee dans le dossier upload."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        upload = os.path.join(self.DATA_DIR, "assets", "musique_fond.mp3")
        with patch("telephonia.paths.os.path.exists", side_effect=lambda p: p == upload):
            result = get_music_path()
        assert result == upload

    @patch.dict(os.environ, {"RESOURCEPATH": BUNDLE_DIR})
    @patch("telephonia.paths.sys")
    def test_get_music_path_bundle_fallback(self, mock_sys):
        """En py2app, fallback vers assets bundle si pas d'upload."""
        mock_sys.frozen = "macosx_app"
        mock_sys.executable = self.EXECUTABLE
        bundle_music = os.path.join(self.BUNDLE_DIR, "assets", "musique_fond.mp3")

        def exists_side(path):
            return path == bundle_music

        with patch("telephonia.paths.os.path.exists", side_effect=exists_side):
            result = get_music_path()
        assert result == bundle_music
