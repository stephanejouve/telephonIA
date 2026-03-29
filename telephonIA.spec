# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec pour telephonIA — bundle autonome."""

import os
import platform

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# ffmpeg.exe embarque (Windows uniquement)
ffmpeg_binary = os.path.join(PROJECT_ROOT, "scripts", "ffmpeg", "ffmpeg.exe")
binaries = []
if platform.system() == "Windows" and os.path.exists(ffmpeg_binary):
    binaries.append((ffmpeg_binary, "."))

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
