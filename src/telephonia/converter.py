"""Convertisseur G.729 vers WAV telephonie."""

import os
import shutil
import subprocess
import sys


def check_ffmpeg() -> str:
    """Verifie que ffmpeg est installe et retourne son chemin.

    Raises:
        SystemExit: Si ffmpeg n'est pas trouve.
    """
    path = shutil.which("ffmpeg")
    if not path:
        print("Erreur : ffmpeg non trouve dans le PATH.")
        print("Installez-le :")
        print("  macOS  : brew install ffmpeg")
        print("  Windows: winget install ffmpeg")
        print("  Linux  : sudo apt-get install ffmpeg")
        sys.exit(1)
    return path


def convert_g729_to_wav(input_path: str, output_path: str) -> str:
    """Convertit un fichier G.729 en WAV telephonie (16kHz mono 16bit).

    Args:
        input_path: Chemin du fichier G.729 source.
        output_path: Chemin du fichier WAV de sortie.

    Returns:
        Chemin du fichier WAV genere.

    Raises:
        FileNotFoundError: Si le fichier source n'existe pas.
        RuntimeError: Si la conversion echoue.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    ffmpeg = check_ffmpeg()

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        input_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-sample_fmt",
        "s16",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Erreur ffmpeg : {result.stderr}")

    return output_path


def convert_batch(input_dir: str, output_dir: str) -> list[dict]:
    """Convertit tous les fichiers G.729 d'un repertoire.

    Args:
        input_dir: Repertoire contenant les fichiers G.729.
        output_dir: Repertoire de sortie pour les fichiers WAV.

    Returns:
        Liste de dictionnaires {"input": str, "output": str, "status": str}.
    """
    os.makedirs(output_dir, exist_ok=True)

    extensions = (".g729", ".g729a", ".G729")
    results = []

    for filename in sorted(os.listdir(input_dir)):
        if not any(filename.endswith(ext) for ext in extensions):
            continue

        input_path = os.path.join(input_dir, filename)
        wav_name = os.path.splitext(filename)[0] + ".wav"
        output_path = os.path.join(output_dir, wav_name)

        try:
            convert_g729_to_wav(input_path, output_path)
            size_kb = os.path.getsize(output_path) / 1024
            results.append(
                {
                    "input": filename,
                    "output": wav_name,
                    "status": f"OK ({size_kb:.0f} Ko)",
                }
            )
        except (RuntimeError, FileNotFoundError) as e:
            results.append(
                {
                    "input": filename,
                    "output": wav_name,
                    "status": f"ERREUR: {e}",
                }
            )

    return results


def main():
    """Point d'entree CLI pour le convertisseur G.729 -> WAV."""
    print("telephonIA — Convertisseur G.729 -> WAV")
    print("=" * 50)

    check_ffmpeg()

    print("\nMode :")
    print("  [1] Convertir un fichier")
    print("  [2] Convertir un dossier entier")
    choice = input("\nChoix (1/2) : ").strip()

    if choice == "2":
        input_dir = input("Dossier source (G.729) : ").strip()
        if not os.path.isdir(input_dir):
            print(f"Erreur : dossier introuvable ({input_dir})")
            sys.exit(1)

        output_dir = input(f"Dossier sortie (WAV) [{input_dir}] : ").strip()
        if not output_dir:
            output_dir = input_dir

        print("\nConversion en cours...\n")
        results = convert_batch(input_dir, output_dir)

        if not results:
            print("Aucun fichier G.729 trouve.")
            sys.exit(0)

        for r in results:
            print(f"  {r['input']} -> {r['output']} [{r['status']}]")
        print(f"\n{len(results)} fichiers traites.")

    else:
        input_path = input("Fichier G.729 source : ").strip()
        if not os.path.exists(input_path):
            print(f"Erreur : fichier introuvable ({input_path})")
            sys.exit(1)

        default_output = os.path.splitext(input_path)[0] + ".wav"
        output_path = input(f"Fichier WAV sortie [{default_output}] : ").strip()
        if not output_path:
            output_path = default_output

        print("\nConversion en cours...")
        try:
            convert_g729_to_wav(input_path, output_path)
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  [OK] {output_path} ({size_kb:.0f} Ko)")
        except RuntimeError as e:
            print(f"  [ERREUR] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
