"""Orchestrateur : generation complete des messages SVI."""

import io
import logging
import os
import sys

import keyring
from pydub import AudioSegment

from telephonia.config import SVIMessage, get_default_messages
from telephonia.mixer import export_telephony, mix_voice_with_music
from telephonia.paths import get_music_path, get_output_dir
from telephonia.tts import TTSError
from telephonia.tts_provider import TTSProvider, create_tts_provider

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Erreur lors de la generation d'un message SVI."""


class SVIGenerator:
    """Orchestrateur de generation de messages SVI.

    Args:
        tts: Client TTS pour la synthese vocale.
        music_path: Chemin vers la musique de fond (optionnel).
        output_dir: Repertoire de sortie pour les fichiers generes.
    """

    def __init__(
        self,
        tts: TTSProvider,
        music_path: str | None,
        output_dir: str,
        voice_format: str = "mp3",
    ):
        self.tts = tts
        self.music_path = music_path
        self.output_dir = output_dir
        self.voice_format = voice_format

    def _process_audio(self, message: SVIMessage, voice_audio: bytes) -> dict:
        """Mixe et exporte un audio voix en WAV telephonie.

        Args:
            message: Configuration du message SVI.
            voice_audio: Contenu audio voix en bytes.

        Returns:
            Dictionnaire {"name": str, "wav": str}.

        Raises:
            GenerationError: Si le mixage ou l'export echoue.
        """
        try:
            if message.background_music:
                mixed = mix_voice_with_music(
                    voice_audio,
                    message.background_music,
                    music_volume_db=message.music_volume_db,
                    voice_format=self.voice_format,
                )
            else:
                mixed = AudioSegment.from_file(io.BytesIO(voice_audio), format=self.voice_format)
        except (FileNotFoundError, IOError) as exc:
            raise GenerationError(f"Mixage echoue pour '{message.name}' : {exc}") from exc

        wav_path = os.path.join(self.output_dir, f"{message.name}.wav")
        try:
            export_telephony(mixed, wav_path)
        except IOError as exc:
            raise GenerationError(f"Export echoue pour '{message.name}' : {exc}") from exc

        return {"name": message.name, "wav": wav_path}

    def generate_message(self, message: SVIMessage) -> dict:
        """Genere un message SVI complet (TTS + mix optionnel + export).

        Args:
            message: Configuration du message SVI.

        Returns:
            Dictionnaire avec les chemins des fichiers generes :
            {"name": str, "wav": str}

        Raises:
            GenerationError: Si la synthese, le mixage ou l'export echoue.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        try:
            voice_audio = self.tts.synthesize(message.text)
        except TTSError as exc:
            raise GenerationError(f"Synthese vocale echouee pour '{message.name}' : {exc}") from exc

        return self._process_audio(message, voice_audio)

    def generate_all(self, messages: list[SVIMessage] | None = None) -> list[dict]:
        """Genere tous les messages SVI avec batch TTS.

        Args:
            messages: Liste de messages a generer. Si None, utilise les messages par defaut.

        Returns:
            Liste de dictionnaires avec les chemins des fichiers generes
            ou les erreurs par message.
        """
        if messages is None:
            messages = get_default_messages(music_path=self.music_path)

        os.makedirs(self.output_dir, exist_ok=True)

        texts = [m.text for m in messages]
        try:
            all_audio = self.tts.synthesize_batch(texts)
        except TTSError as exc:
            raise GenerationError(f"Synthese batch echouee : {exc}") from exc

        results = []
        for message, audio_or_error in zip(messages, all_audio):
            if isinstance(audio_or_error, Exception):
                logger.error("[ERREUR] %s : %s", message.name, audio_or_error)
                results.append({"name": message.name, "error": str(audio_or_error)})
            else:
                result = self._process_audio(message, audio_or_error)
                results.append(result)
                logger.info("[OK] %s -> %s", message.name, result["wav"])

        return results


def get_api_key() -> str:
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

    logger.warning("Cle API ElevenLabs introuvable dans le trousseau systeme.")
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

    # Selectionner le provider TTS
    tts_provider = create_tts_provider()

    # Configuration
    music_path = get_music_path()
    output_dir = get_output_dir()

    if music_path is None:
        print("Info : musique de fond non trouvee")
        print("  Les messages seront generes sans musique de fond.")

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
    generator = SVIGenerator(
        tts=tts_provider,
        music_path=music_path,
        output_dir=output_dir,
        voice_format=tts_provider.voice_format,
    )

    print("\nGeneration des messages SVI...\n")

    results = generator.generate_all(messages=messages)

    print(f"\n{len(results)} messages generes avec succes.")
    for r in results:
        print(f"  - {r['name']}: {r['wav']}")


if __name__ == "__main__":
    main()
