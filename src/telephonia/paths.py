"""Source de verite pour tous les chemins du projet."""

import os
import platform
import sys


def _is_pyinstaller() -> bool:
    """Detecte un contexte PyInstaller (Windows .exe)."""
    return getattr(sys, "frozen", False) is True


def _is_py2app() -> bool:
    """Detecte un contexte py2app (macOS .app)."""
    return getattr(sys, "frozen", False) == "macosx_app"


def _is_frozen() -> bool:
    """Detecte tout contexte bundle (PyInstaller ou py2app)."""
    return bool(getattr(sys, "frozen", False))


def _get_exe_dir() -> str:
    """Retourne le dossier contenant l'executable (bundle uniquement)."""
    return os.path.dirname(os.path.abspath(sys.executable))


def _get_user_data_dir() -> str:
    """Retourne le repertoire de donnees utilisateur pour le bundle Windows.

    Utilise %LOCALAPPDATA%/telephonIA (toujours accessible en ecriture,
    meme si le .exe est dans C:\\Program Files).
    """
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(base, "telephonIA")


def _get_macos_bundle_dir() -> str:
    """Retourne le dossier python_backend/ dans le bundle macOS.

    RESOURCEPATH (defini par le wrapper shell ou py2app) est la source de verite.
    Fallback sur sys.executable si absent (ne devrait pas arriver en bundle).
    """
    resource_path = os.environ.get("RESOURCEPATH")
    if resource_path:
        return resource_path
    return os.path.dirname(os.path.abspath(sys.executable))


def _get_macos_data_dir() -> str:
    """Retourne ~/Library/Application Support/telephonIA/ (writable)."""
    return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "telephonIA")


def get_project_root() -> str:
    """Retourne la racine du projet.

    En bundle py2app, retourne le dossier python_backend/.
    En bundle PyInstaller, retourne sys._MEIPASS.
    En dev, remonte 2 niveaux depuis telephonia/ (src/telephonia -> racine).
    """
    if _is_py2app():
        return _get_macos_bundle_dir()
    if _is_pyinstaller():
        return sys._MEIPASS
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_assets_dir() -> str:
    """Retourne le chemin du dossier assets.

    En py2app : {bundle_dir}/assets (lecture seule dans le .app).
    En PyInstaller : a cote de l'executable.
    En dev : sous la racine du projet.
    """
    if _is_py2app():
        return os.path.join(_get_macos_bundle_dir(), "assets")
    if _is_frozen():
        return os.path.join(_get_exe_dir(), "assets")
    return os.path.join(get_project_root(), "assets")


def get_music_upload_dir() -> str:
    """Retourne le dossier pour les uploads musique (toujours writable).

    En py2app : ~/Library/Application Support/telephonIA/assets.
    En bundle Windows : %LOCALAPPDATA%/telephonIA/assets.
    En dev : {racine}/assets.
    """
    if _is_py2app():
        return os.path.join(_get_macos_data_dir(), "assets")
    if _is_frozen() and platform.system() == "Windows":
        return os.path.join(_get_user_data_dir(), "assets")
    return os.path.join(get_project_root(), "assets")


def get_music_path() -> str | None:
    """Retourne le chemin vers la musique de fond, ou None si absente.

    Cherche dans l'ordre :
    1. Dossier upload (writable, LOCALAPPDATA sur Windows bundle)
    2. A cote de l'exe (lecture seule OK dans Program Files)
    """
    # 1. Dossier upload (prioritaire — fichier depose par l'utilisateur)
    upload_path = os.path.join(get_music_upload_dir(), "musique_fond.mp3")
    if os.path.exists(upload_path):
        return upload_path

    # 2. A cote de l'exe ou dans le projet (livraison initiale)
    assets_path = os.path.join(get_assets_dir(), "musique_fond.mp3")
    if os.path.exists(assets_path):
        return assets_path

    return None


def get_output_dir() -> str:
    """Retourne le chemin du dossier de sortie.

    En py2app : ~/Library/Application Support/telephonIA/output.
    En bundle Windows : %LOCALAPPDATA%/telephonIA/output.
    En dev : sous la racine du projet.
    """
    if _is_py2app():
        return os.path.join(_get_macos_data_dir(), "output")
    if _is_frozen() and platform.system() == "Windows":
        return os.path.join(_get_user_data_dir(), "output")
    return os.path.join(get_project_root(), "output")


def get_static_dir() -> str:
    """Retourne le chemin vers les fichiers statiques (build React).

    En py2app : {bundle_dir}/static.
    En PyInstaller : {MEIPASS}/static.
    En dev : web/static.
    """
    if _is_py2app():
        return os.path.join(_get_macos_bundle_dir(), "static")
    if _is_pyinstaller():
        return os.path.join(sys._MEIPASS, "static")
    return os.path.join(os.path.dirname(__file__), "web", "static")


def get_ffmpeg_path() -> str:
    """Retourne le chemin ffmpeg.

    En py2app : ffmpeg dans le bundle macOS.
    En PyInstaller : ffmpeg.exe dans _MEIPASS.
    En dev : ffmpeg systeme.
    """
    if _is_py2app():
        return os.path.join(_get_macos_bundle_dir(), "ffmpeg")
    if _is_pyinstaller():
        return os.path.join(sys._MEIPASS, "ffmpeg.exe")
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Retourne le chemin ffprobe.

    ffprobe est un binaire distinct de ffmpeg — pydub en a besoin pour
    introspecter les fichiers audio (duree, codec, channels). Reutiliser
    ffmpeg comme ffprobe fonctionne par coincidence sur certains cas mais
    casse des qu'une commande specifique a ffprobe est invoquee.

    En py2app : ffprobe dans le bundle macOS.
    En PyInstaller : ffprobe.exe dans _MEIPASS.
    En dev : ffprobe systeme.
    """
    if _is_py2app():
        return os.path.join(_get_macos_bundle_dir(), "ffprobe")
    if _is_pyinstaller():
        return os.path.join(sys._MEIPASS, "ffprobe.exe")
    return "ffprobe"
