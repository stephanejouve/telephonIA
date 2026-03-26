"""Orchestrateur : generation complete des messages SVI."""

import os
import sys

import keyring

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
    """Recupere la cle API ElevenLabs depuis le trousseau systeme.

    Utilise keyring (multiplateforme) :
    - macOS : Trousseau d'acces (Keychain)
    - Windows : Credential Manager
    - Linux : Secret Service (GNOME Keyring / KWallet)

    Returns:
        La cle API.

    Raises:
        SystemExit: Si la cle n'est pas trouvee dans le trousseau.
    """
    api_key = keyring.get_password("elevenlabs_api_key", "telephonia")
    if api_key:
        return api_key

    print("Erreur : cle API ElevenLabs introuvable dans le trousseau systeme.")
    print("Ajoutez-la avec :")
    print("  keyring set elevenlabs_api_key telephonia")
    sys.exit(1)


MESSAGES_INFO = [
    {
        "name": "pre_decroche",
        "label": "Pre-decroche",
        "description": "Court message d'accueil a la prise d'appel",
        "has_music": False,
    },
    {
        "name": "attente",
        "label": "Attente",
        "description": "Message diffuse pendant la mise en attente",
        "has_music": True,
    },
    {
        "name": "repondeur",
        "label": "Repondeur",
        "description": "Message du repondeur (hors horaires)",
        "has_music": False,
    },
]


def _input_multiline(prompt: str) -> str:
    """Saisie multiligne. Ligne vide pour terminer."""
    print(prompt)
    print("  (Ligne vide pour terminer)")
    lines = []
    while True:
        line = input("  > ")
        if not line:
            break
        lines.append(line)
    return " ".join(lines)


def _prompt_messages(music_path: str | None) -> list[SVIMessage]:
    """Formulaire interactif pour saisir les 3 messages SVI."""
    messages = []
    for info in MESSAGES_INFO:
        print(f"\n--- {info['label']} ---")
        print(f"  ({info['description']})")
        if info["has_music"] and music_path:
            print("  * Musique de fond : oui")

        text = _input_multiline("  Texte du message :")

        if not text.strip():
            print("  [!] Texte vide, message ignore.")
            continue

        messages.append(
            SVIMessage(
                name=info["name"],
                text=text,
                target_duration=0,
                background_music=music_path if info["has_music"] else None,
                music_volume_db=-15.0,
            )
        )

    return messages


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

    # Choix du mode
    print("\nMode de saisie :")
    print("  [1] Textes par defaut (Les Saveurs du Terroir)")
    print("  [2] Saisir les textes manuellement")
    choice = input("\nChoix (1/2) : ").strip()

    if choice == "2":
        messages = _prompt_messages(music_path)
        if not messages:
            print("Aucun message saisi. Abandon.")
            sys.exit(0)
    else:
        messages = get_default_messages(music_path=music_path)

    # Recapitulatif
    print(f"\nRepertoire de sortie : {output_dir}")
    print(f"Messages a generer : {len(messages)}\n")
    for msg in messages:
        music_info = " [+ musique]" if msg.background_music else ""
        print(f"  - {msg.name}{music_info}")
        # Afficher les 80 premiers caracteres du texte
        preview = msg.text[:80] + "..." if len(msg.text) > 80 else msg.text
        print(f"    {preview}")

    confirm = input("\nGenerer ? (O/n) : ").strip().lower()
    if confirm == "n":
        print("Abandon.")
        sys.exit(0)

    # Generation
    tts = ElevenLabsTTS(api_key=api_key, voice_id=voice_id)
    generator = SVIGenerator(tts=tts, music_path=music_path, output_dir=output_dir)

    print("\nGeneration des messages SVI...\n")

    results = generator.generate_all(messages=messages)

    print(f"\n{len(results)} messages generes avec succes.")
    for r in results:
        print(f"  - {r['name']}: {r['wav']}")


if __name__ == "__main__":
    main()
