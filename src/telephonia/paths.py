"""Source de verite pour tous les chemins du projet."""

import os
import platform
import sys


def get_project_root() -> str:
    """Retourne la racine du projet.

    En bundle PyInstaller, retourne sys._MEIPASS.
    En dev, remonte 2 niveaux depuis telephonia/ (src/telephonia -> racine).
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


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


def get_assets_dir() -> str:
    """Retourne le chemin du dossier assets.

    En bundle, cherche a cote de l'executable (lecture seule OK).
    En dev, sous la racine du projet.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(_get_exe_dir(), "assets")
    return os.path.join(get_project_root(), "assets")


def get_music_path() -> str | None:
    """Retourne le chemin vers la musique de fond, ou None si absente.

    En bundle Windows, cherche d'abord a cote de l'exe, puis dans
    le dossier utilisateur (LOCALAPPDATA).
    """
    # Chemin principal (a cote de l'exe ou dans le projet)
    path = os.path.join(get_assets_dir(), "musique_fond.mp3")
    if os.path.exists(path):
        return path

    # Fallback : dossier utilisateur (bundle Windows)
    if getattr(sys, "frozen", False) and platform.system() == "Windows":
        alt = os.path.join(_get_user_data_dir(), "assets", "musique_fond.mp3")
        if os.path.exists(alt):
            return alt

    return None


def get_output_dir() -> str:
    """Retourne le chemin du dossier de sortie.

    En bundle Windows, utilise %LOCALAPPDATA%/telephonIA/output pour eviter
    les problemes de permissions dans C:\\Program Files.
    En dev, sous la racine du projet.
    """
    if getattr(sys, "frozen", False) and platform.system() == "Windows":
        return os.path.join(_get_user_data_dir(), "output")
    return os.path.join(get_project_root(), "output")


def get_static_dir() -> str:
    """Retourne le chemin vers les fichiers statiques (build React).

    En bundle PyInstaller, pointe vers {MEIPASS}/static.
    En dev, pointe vers web/static.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "static")
    return os.path.join(os.path.dirname(__file__), "web", "static")


def get_ffmpeg_path() -> str:
    """Retourne le chemin ffmpeg.

    En bundle PyInstaller, ffmpeg.exe est embarque dans _MEIPASS.
    En dev, on utilise le ffmpeg systeme.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "ffmpeg.exe")
    return "ffmpeg"
