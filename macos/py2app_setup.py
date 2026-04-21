"""Configuration py2app pour builder le backend Python de telephonIA."""

import os
import shutil
import sys

from setuptools import setup

# Chemins relatifs depuis macos/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ajouter src/ au path pour que py2app trouve le package telephonia
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
STATIC_DIR = os.path.join(PROJECT_ROOT, "src", "telephonia", "web", "static")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Trouver ffmpeg + ffprobe. pydub a besoin des DEUX binaires : ffmpeg pour
# l'encodage/mixage, ffprobe pour l'introspection (duree, codec, channels).
# Echec build si l'un manque — evite un bundle silencieusement incomplet
# qui crashe au premier mixage TTS avec "Le fichier specifie est introuvable".
FFMPEG_PATH = shutil.which("ffmpeg")
FFPROBE_PATH = shutil.which("ffprobe")
missing = [(n, p) for n, p in (("ffmpeg", FFMPEG_PATH), ("ffprobe", FFPROBE_PATH)) if not p]
if missing:
    names = ", ".join(n for n, _ in missing)
    print(
        f"ERREUR: {names} introuvable dans le PATH. "
        "Installer via `brew install ffmpeg` (inclut ffprobe).",
        file=sys.stderr,
    )
    sys.exit(1)

# Fichiers de donnees a inclure dans le bundle
data_files = []

# Build React (static/)
if os.path.isdir(STATIC_DIR):
    for dirpath, _dirnames, filenames in os.walk(STATIC_DIR):
        if filenames:
            rel = os.path.relpath(dirpath, STATIC_DIR)
            dest = os.path.join("static", rel) if rel != "." else "static"
            data_files.append((dest, [os.path.join(dirpath, f) for f in filenames]))

# Assets (musique de fond etc.)
if os.path.isdir(ASSETS_DIR):
    asset_files = [
        os.path.join(ASSETS_DIR, f)
        for f in os.listdir(ASSETS_DIR)
        if not f.startswith(".")
    ]
    if asset_files:
        data_files.append(("assets", asset_files))

# ffmpeg + ffprobe binaires
data_files.append((".", [FFMPEG_PATH, FFPROBE_PATH]))

APP = [os.path.join(PROJECT_ROOT, "src", "telephonia", "web", "app.py")]

OPTIONS = {
    "argv_emulation": False,
    # semi-standalone : ne bundle pas le framework Python (evite les dylib
    # cassees de Homebrew). L'app depend de Python 3.11 installe sur la machine.
    # Pour un build full-standalone, il faudra `brew reinstall python@3.11`.
    "semi_standalone": True,
    "packages": [
        "telephonia",
        "uvicorn",
        "fastapi",
        "starlette",
        "pydantic",
        "edge_tts",
        "pydub",
        "keyring",
        "multipart",
        "anyio",
        "httptools",
        "dotenv",
    ],
    "includes": [
        # uvicorn internals
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # starlette internals
        "starlette.responses",
        "starlette.routing",
        "starlette.middleware",
        # audioop pour Python 3.13+
        "audioop",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "scipy",
        "numpy",
        "PIL",
        "PyQt5",
        "wx",
        # _decimal.so est casse sur cette install (libmpdec.3 -> .4 upgrade)
        # Le fallback Python pur (decimal) fonctionne sans probleme
        "_decimal",
    ],
    "plist": {
        "CFBundleName": "telephonIA Backend",
        "CFBundleIdentifier": "eu.alliancejr.telephonIA.backend",
    },
}

setup(
    name="telephonia-web",
    app=APP,
    data_files=data_files,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
