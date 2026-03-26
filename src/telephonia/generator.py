"""Orchestrateur : generation complete des messages SVI."""

import os
import subprocess
import sys

from telephonia.config import SVIMessage, get_default_messages
from telephonia.mixer import export_telephony, mix_voice_with_music
from telephonia.tts import ElevenLabsTTS


class SVIGenerator:
    """Orchestrateur de generation de messages SVI.

    Args:
        tts: Client TTS pour la synthese vocale.
        music_path: Chemin vers la musique de fond (optionnel).
        output_dir: Repertoire de sortie pour les fichiers generes.
    """

    def __init__(
        self,
        tts: ElevenLabsTTS,
        music_path: str | None,
        output_dir: str,
        voice_format: str = "mp3",
    ):
        self.tts = tts
        self.music_path = music_path
        self.output_dir = output_dir
        self.voice_format = voice_format

    def generate_message(self, message: SVIMessage) -> dict:
        """Genere un message SVI complet (TTS + mix optionnel + export).

        Args:
            message: Configuration du message SVI.

        Returns:
            Dictionnaire avec les chemins des fichiers generes :
            {"name": str, "wav": str}
        """
        os.makedirs(self.output_dir, exist_ok=True)

        # Synthese vocale
        voice_audio = self.tts.synthesize(message.text)

        # Mix avec musique si configure
        if message.background_music:
            from pydub import AudioSegment

            mixed = mix_voice_with_music(
                voice_audio,
                message.background_music,
                music_volume_db=message.music_volume_db,
                voice_format=self.voice_format,
            )
        else:
            import io

            from pydub import AudioSegment

            mixed = AudioSegment.from_file(io.BytesIO(voice_audio), format=self.voice_format)

        # Export WAV telephonie (LPCM16 16kHz mono 16bit)
        wav_path = os.path.join(self.output_dir, f"{message.name}.wav")
        export_telephony(mixed, wav_path)

        return {"name": message.name, "wav": wav_path}

    def generate_all(self, messages: list[SVIMessage] | None = None) -> list[dict]:
        """Genere tous les messages SVI.

        Args:
            messages: Liste de messages a generer. Si None, utilise les messages par defaut.

        Returns:
            Liste de dictionnaires avec les chemins des fichiers generes.
        """
        if messages is None:
            messages = get_default_messages(music_path=self.music_path)

        results = []
        for message in messages:
            result = self.generate_message(message)
            results.append(result)
            print(f"  [OK] {message.name} -> {result['wav']}")

        return results


def _get_api_key() -> str:
    """Recupere la cle API ElevenLabs depuis le trousseau macOS.

    Returns:
        La cle API.

    Raises:
        SystemExit: Si la cle n'est pas trouvee dans le trousseau.
    """
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-l", "elevenlabs_api_key", "-w"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Erreur : cle API ElevenLabs introuvable dans le trousseau macOS.")
        print("Ajoutez-la avec :")
        print(
            '  security add-generic-password -s "elevenlabs_api_key" -a "telephonia" -w "VOTRE_CLE"'
        )
        sys.exit(1)


def main():
    """Point d'entree CLI pour la generation des messages SVI."""
    print("telephonIA — Generateur de bandes sonores SVI")
    print("=" * 50)

    # Recuperer la cle API
    api_key = _get_api_key()

    # Configuration
    voice_id = "XB0fDUnXU5powFXDhCwa"  # Charlotte (voix FR)
    music_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "musique_fond.mp3")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")

    # Normaliser les chemins
    music_path = os.path.normpath(music_path)
    output_dir = os.path.normpath(output_dir)

    if not os.path.exists(music_path):
        print(f"Info : musique de fond non trouvee ({music_path})")
        print("  Les messages seront generes sans musique de fond.")
        music_path = None

    # Generation
    tts = ElevenLabsTTS(api_key=api_key, voice_id=voice_id)
    generator = SVIGenerator(tts=tts, music_path=music_path, output_dir=output_dir)

    print(f"\nRepertoire de sortie : {output_dir}")
    print("Generation des messages SVI...\n")

    results = generator.generate_all()

    print(f"\n{len(results)} messages generes avec succes.")
    for r in results:
        print(f"  - {r['name']}: {r['wav']}")


if __name__ == "__main__":
    main()
