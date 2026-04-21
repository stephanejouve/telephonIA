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
FFPROBE_EXE = os.path.join(FFMPEG_DIR, "ffprobe.exe")
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
# Fichiers a extraire depuis l'archive gyan.dev — cible les 2 binaires exiges
# par telephonIA.spec. pydub a besoin des DEUX : ffmpeg pour l'encodage,
# ffprobe pour l'introspection (duree, codec, channels).
FFMPEG_ARCHIVE_TARGETS = {
    "bin/ffmpeg.exe": FFMPEG_EXE,
    "bin/ffprobe.exe": FFPROBE_EXE,
}
SPEC_FILE = os.path.join(PROJECT_ROOT, "telephonIA.spec")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")


def download_ffmpeg():
    """Telecharge et extrait ffmpeg.exe + ffprobe.exe depuis gyan.dev."""
    if os.path.exists(FFMPEG_EXE) and os.path.exists(FFPROBE_EXE):
        print(f"ffmpeg.exe + ffprobe.exe deja presents : {FFMPEG_DIR}")
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

    print("Extraction de ffmpeg.exe + ffprobe.exe...")
    extracted = set()
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            for suffix, dest in FFMPEG_ARCHIVE_TARGETS.items():
                if name.endswith(suffix):
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        dst.write(src.read())
                    print(f"  Extrait : {dest}")
                    extracted.add(suffix)
                    break

    missing = set(FFMPEG_ARCHIVE_TARGETS) - extracted
    if missing:
        print(f"ERREUR : binaires introuvables dans l'archive : {sorted(missing)}")
        sys.exit(1)

    os.remove(zip_path)
    print("ffmpeg.exe + ffprobe.exe prets.")


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
        if not os.path.exists(FFPROBE_EXE):
            print("  Info : ffprobe.exe absent (normal hors Windows)")

    run_pyinstaller(console=console)
    verify_output()


if __name__ == "__main__":
    main()
