"""Source de verite pour tous les chemins du projet."""

import os
import sys


def get_project_root() -> str:
    """Retourne la racine du projet.

    En bundle PyInstaller, retourne sys._MEIPASS.
    En dev, remonte 2 niveaux depuis telephonia/ (src/telephonia -> racine).
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_assets_dir() -> str:
    """Retourne le chemin du dossier assets."""
    return os.path.join(get_project_root(), "assets")


def get_music_path() -> str | None:
    """Retourne le chemin vers la musique de fond, ou None si absente."""
    path = os.path.join(get_assets_dir(), "musique_fond.mp3")
    return path if os.path.exists(path) else None


def get_output_dir() -> str:
    """Retourne le chemin du dossier de sortie."""
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
