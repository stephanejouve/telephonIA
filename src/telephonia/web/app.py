"""Point d'entree serveur web telephonIA."""

import os
import socket
import sys
import webbrowser

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from telephonia.web.api import router


def get_base_path() -> str:
    """Retourne le chemin de base selon le contexte (dev vs bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(__file__)


def get_static_path() -> str:
    """Retourne le chemin vers les fichiers statiques (build React)."""
    return os.path.join(get_base_path(), "static")


def get_ffmpeg_path() -> str:
    """Retourne le chemin ffmpeg selon le contexte.

    En bundle PyInstaller, ffmpeg.exe est embarque dans _MEIPASS.
    En dev, on utilise le ffmpeg systeme.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "ffmpeg.exe")
    return "ffmpeg"


STATIC_DIR = get_static_path()


def create_app() -> FastAPI:
    """Cree et configure l'application FastAPI."""
    app = FastAPI(title="telephonIA", version="0.1.0")
    app.include_router(router)

    # Servir les fichiers statiques (build React) si le dossier existe et contient des fichiers
    if os.path.isdir(STATIC_DIR) and any(f for f in os.listdir(STATIC_DIR) if f != ".gitkeep"):
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app


def find_free_port() -> int:
    """Trouve un port libre en laissant l'OS en attribuer un."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def get_lan_ip() -> str:
    """Retourne l'adresse IP LAN de la machine."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "127.0.0.1"


def _configure_ffmpeg():
    """Configure pydub pour utiliser le ffmpeg embarque si en bundle."""
    if getattr(sys, "frozen", False):
        from pydub import AudioSegment

        ffmpeg = get_ffmpeg_path()
        AudioSegment.converter = ffmpeg
        AudioSegment.ffprobe = ffmpeg


def main():
    """Lance le serveur web telephonIA."""
    _configure_ffmpeg()
    port = find_free_port()
    lan_ip = get_lan_ip()

    local_url = f"http://localhost:{port}"
    lan_url = f"http://{lan_ip}:{port}"

    print("telephonIA — Interface web")
    print("=" * 50)
    print(f"  Local : {local_url}")
    print(f"  LAN   : {lan_url}")
    print("=" * 50)

    webbrowser.open(local_url)

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
