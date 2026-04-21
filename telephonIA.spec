# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec pour telephonIA — bundle autonome."""

import os
import platform

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# ffmpeg.exe + ffprobe.exe embarques (Windows uniquement). Les deux sont
# necessaires : ffmpeg pour l'encodage/mixage, ffprobe pour l'introspection
# (duree, codec, channels) appelee par pydub. Build bloquant si l'un manque
# — sinon le .exe produit crashe silencieusement au premier mixage TTS
# avec `[WinError 2] Le fichier specifie est introuvable`.
binaries = []
if platform.system() == "Windows":
    ffmpeg_binary = os.path.join(PROJECT_ROOT, "scripts", "ffmpeg", "ffmpeg.exe")
    ffprobe_binary = os.path.join(PROJECT_ROOT, "scripts", "ffmpeg", "ffprobe.exe")
    missing = [p for p in (ffmpeg_binary, ffprobe_binary) if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            "Binaires ffmpeg/ffprobe manquants pour le build Windows :\n  "
            + "\n  ".join(missing)
            + "\n\nTelecharger ffmpeg-release-essentials.zip depuis "
            "https://www.gyan.dev/ffmpeg/builds/ et placer ffmpeg.exe + "
            "ffprobe.exe dans scripts/ffmpeg/. Voir docs/DEPLOIEMENT_WINDOWS.md."
        )
    binaries.append((ffmpeg_binary, "."))
    binaries.append((ffprobe_binary, "."))

# Fichiers statiques (build React)
static_dir = os.path.join(PROJECT_ROOT, "src", "telephonia", "web", "static")
datas = []
if os.path.isdir(static_dir):
    datas.append((static_dir, "static"))

# Collecter tous les fichiers edge-tts AVANT Analysis
# pour que les 2-tuples soient normalises par Analysis (et non ajoutes apres)
from PyInstaller.utils.hooks import collect_all

edge_datas, edge_binaries, edge_hiddenimports = collect_all("edge_tts")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "src", "telephonia", "web", "app.py")],
    pathex=[os.path.join(PROJECT_ROOT, "src")],
    binaries=binaries + edge_binaries,
    datas=datas + edge_datas,
    hiddenimports=[
        "edge_tts",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "telephonia.paths",
        "telephonia.web.api",
        "telephonia.web.middleware",
        "telephonia.config",
        "telephonia.generator",
        "telephonia.mixer",
        "telephonia.tts",
        "telephonia.tts_provider",
    ]
    + edge_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="telephonIA",
    icon=os.path.join(PROJECT_ROOT, "scripts", "icons", "telephonIA.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Mettre console=True pour debug, False pour distribution
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
