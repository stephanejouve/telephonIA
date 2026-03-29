"""Point d'entree serveur web telephonIA."""

import os
import socket
import webbrowser

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from telephonia.paths import get_ffmpeg_path, get_static_dir
from telephonia.web.api import router
from telephonia.web.middleware import LoggingMiddleware


def create_app() -> FastAPI:
    """Cree et configure l'application FastAPI."""
    app = FastAPI(title="telephonIA", version="0.1.0")
    app.add_middleware(LoggingMiddleware)
    app.include_router(router)

    # Servir les fichiers statiques (build React) si le dossier existe et contient des fichiers
    static_dir = get_static_dir()
    if os.path.isdir(static_dir) and any(f for f in os.listdir(static_dir) if f != ".gitkeep"):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

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
    if get_ffmpeg_path() != "ffmpeg":
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
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    main()
