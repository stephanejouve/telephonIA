"""Script de build du bundle PyInstaller pour telephonIA.

Telecharge ffmpeg.exe si absent, puis lance PyInstaller pour creer
un .exe autonome incluant Python, ffmpeg, edge-tts et le frontend React.

Usage : poetry run python scripts/build_bundle.py [--console]
"""

import os
import platform
import subprocess
import sys
import zipfile

import requests

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FFMPEG_DIR = os.path.join(PROJECT_ROOT, "scripts", "ffmpeg")
FFMPEG_EXE = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
SPEC_FILE = os.path.join(PROJECT_ROOT, "telephonIA.spec")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")


def download_ffmpeg():
    """Telecharge et extrait ffmpeg.exe depuis gyan.dev."""
    if os.path.exists(FFMPEG_EXE):
        print(f"ffmpeg.exe deja present : {FFMPEG_EXE}")
        return

    print("Telechargement de ffmpeg...")
    os.makedirs(FFMPEG_DIR, exist_ok=True)
    zip_path = os.path.join(FFMPEG_DIR, "ffmpeg.zip")

    response = requests.get(FFMPEG_URL, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 // total
                print(f"\r  Progression : {pct}%", end="", flush=True)
    print()

    print("Extraction de ffmpeg.exe...")
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("bin/ffmpeg.exe"):
                with zf.open(name) as src, open(FFMPEG_EXE, "wb") as dst:
                    dst.write(src.read())
                print(f"  Extrait : {FFMPEG_EXE}")
                break
        else:
            print("ERREUR : ffmpeg.exe introuvable dans l'archive.")
            sys.exit(1)

    os.remove(zip_path)
    print("ffmpeg.exe pret.")


def run_pyinstaller(console: bool = False):
    """Lance PyInstaller avec le fichier spec."""
    if not os.path.exists(SPEC_FILE):
        print(f"ERREUR : fichier spec introuvable : {SPEC_FILE}")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        SPEC_FILE,
        "--noconfirm",
        "--clean",
        "--distpath",
        DIST_DIR,
    ]

    print(f"Lancement PyInstaller ({'console' if console else 'noconsole'})...")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("ERREUR : PyInstaller a echoue.")
        sys.exit(1)


def verify_output():
    """Verifie que le .exe existe et affiche sa taille."""
    exe_path = os.path.join(DIST_DIR, "telephonIA.exe")
    if not os.path.exists(exe_path):
        # Sur macOS/Linux, le binaire n'a pas d'extension
        exe_path = os.path.join(DIST_DIR, "telephonIA")

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\nBuild reussi !")
        print(f"  Fichier : {exe_path}")
        print(f"  Taille  : {size_mb:.1f} Mo")
    else:
        print("\nERREUR : fichier de sortie introuvable dans dist/")
        sys.exit(1)


def main():
    console = "--console" in sys.argv

    print("=" * 50)
    print("telephonIA — Build bundle PyInstaller")
    print("=" * 50)

    if platform.system() == "Windows":
        download_ffmpeg()
    else:
        print(f"Plateforme : {platform.system()} (ffmpeg systeme utilise)")
        if not os.path.exists(FFMPEG_EXE):
            print("  Info : ffmpeg.exe absent (normal hors Windows)")

    run_pyinstaller(console=console)
    verify_output()


if __name__ == "__main__":
    main()
