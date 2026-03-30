"""Interface commune pour les providers TTS et selection automatique."""

import asyncio
import io
import logging
import re
from abc import ABC, abstractmethod

import edge_tts
import keyring

from telephonia.tts import ElevenLabsTTS, NetworkError, TTSError

logger = logging.getLogger(__name__)


def normalize_text_fr(text: str) -> str:
    """Normalise le texte pour la prononciation francaise en synthese vocale."""
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"\bwww\.", "double vé double vé double vé point ", text)
    text = re.sub(r"\bwww\b", "double vé double vé double vé", text)
    text = re.sub(r"\.com\b", " point com", text)
    text = re.sub(r"\.fr\b", " point fr", text)
    text = re.sub(r"\.org\b", " point org", text)
    text = re.sub(r"\.net\b", " point net", text)
    text = re.sub(r"@", " arobase ", text)
    return text


class TTSProvider(ABC):
    """Interface abstraite pour les providers TTS."""

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Synthetise du texte en audio.

        Args:
            text: Texte a convertir en voix.

        Returns:
            Contenu audio en bytes (MP3).
        """

    @abstractmethod
    def list_voices(self) -> list[dict]:
        """Liste les voix disponibles pour ce provider.

        Returns:
            Liste de dictionnaires {"id": str, "name": str}.
        """

    def synthesize_batch(self, texts: list[str]) -> list[bytes]:
        """Synthetise plusieurs textes. Par defaut, appels sequentiels.

        Args:
            texts: Liste de textes a convertir.

        Returns:
            Liste de contenus audio en bytes.
        """
        return [self.synthesize(t) for t in texts]


class ElevenLabsProvider(TTSProvider):
    """Provider TTS ElevenLabs (premium, necessite cle API).

    Args:
        api_key: Cle API ElevenLabs.
        voice_id: Identifiant de la voix.
        model: Modele TTS.
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str = "XB0fDUnXU5powFXDhCwa",
        model: str = "eleven_multilingual_v2",
    ):
        self.client = ElevenLabsTTS(api_key=api_key, voice_id=voice_id, model=model)
        self.voice_format = "mp3"

    def synthesize(self, text: str) -> bytes:
        """Synthetise via l'API ElevenLabs."""
        return self.client.synthesize(normalize_text_fr(text))

    def list_voices(self) -> list[dict]:
        """Liste les voix ElevenLabs disponibles."""
        voices = self.client.list_voices()
        return [{"id": v["voice_id"], "name": v["name"]} for v in voices]


class EdgeTTSProvider(TTSProvider):
    """Provider TTS Edge (gratuit, sans cle API).

    Args:
        voice: Nom de la voix Edge TTS (defaut: fr-FR-DeniseNeural).
    """

    def __init__(self, voice: str = "fr-FR-DeniseNeural"):
        self.voice = voice
        self.voice_format = "mp3"

    def synthesize(self, text: str) -> bytes:
        """Synthetise via Edge TTS (Microsoft)."""
        try:
            return asyncio.run(self._synthesize_async(text))
        except TTSError:
            raise
        except Exception as exc:
            raise NetworkError(f"Erreur Edge TTS (reseau ou service indisponible) : {exc}") from exc

    def synthesize_batch(self, texts: list[str]) -> list[bytes | Exception]:
        """Batch async — un seul asyncio.run() avec asyncio.gather.

        Args:
            texts: Liste de textes a convertir.

        Returns:
            Liste de bytes (succes) ou Exception (echec) par texte.
        """
        return asyncio.run(self._synthesize_batch_async(texts))

    async def _synthesize_batch_async(self, texts: list[str]) -> list[bytes | Exception]:
        """Implementation async du batch avec gestion d'erreurs granulaire."""
        return await asyncio.gather(
            *[self._synthesize_async(t) for t in texts],
            return_exceptions=True,
        )

    async def _synthesize_async(self, text: str) -> bytes:
        """Implementation async de la synthese Edge TTS."""
        communicate = edge_tts.Communicate(normalize_text_fr(text), voice=self.voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        audio_bytes = buffer.getvalue()
        if not audio_bytes:
            raise TTSError("Edge TTS n'a retourne aucun audio.")
        return audio_bytes

    def list_voices(self) -> list[dict]:
        """Liste les voix Edge TTS francophones (fr-FR)."""
        all_voices = asyncio.run(edge_tts.list_voices())
        return [
            {"id": v["ShortName"], "name": v["FriendlyName"]}
            for v in all_voices
            if v.get("Locale") == "fr-FR"
        ]


def get_elevenlabs_key() -> str | None:
    """Tente de recuperer la cle API ElevenLabs depuis le trousseau.

    Returns:
        La cle API ou None si absente.
    """
    return keyring.get_password("elevenlabs_api_key", "telephonia")


def create_tts_provider(voice: str | None = None) -> TTSProvider:
    """Selectionne automatiquement le provider TTS.

    Si une cle ElevenLabs est configuree dans le trousseau, utilise ElevenLabs.
    Sinon, utilise Edge TTS (gratuit).

    Args:
        voice: Identifiant de la voix a utiliser. Si None, le provider utilise son defaut.

    Returns:
        Instance du provider TTS selectionne.
    """
    api_key = get_elevenlabs_key()
    if api_key:
        logger.info("Provider TTS : ElevenLabs")
        if voice:
            return ElevenLabsProvider(api_key=api_key, voice_id=voice)
        return ElevenLabsProvider(api_key=api_key)

    logger.info("Provider TTS : EdgeTTS (gratuit)")
    if voice:
        return EdgeTTSProvider(voice=voice)
    return EdgeTTSProvider()
