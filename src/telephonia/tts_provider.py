"""Interface commune pour les providers TTS et selection automatique."""

import asyncio
import io
import logging
from abc import ABC, abstractmethod

import edge_tts
import keyring

from telephonia.tts import ElevenLabsTTS, NetworkError, TTSError

logger = logging.getLogger(__name__)


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
        return self.client.synthesize(text)


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
        communicate = edge_tts.Communicate(text, voice=self.voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        audio_bytes = buffer.getvalue()
        if not audio_bytes:
            raise TTSError("Edge TTS n'a retourne aucun audio.")
        return audio_bytes


def get_elevenlabs_key() -> str | None:
    """Tente de recuperer la cle API ElevenLabs depuis le trousseau.

    Returns:
        La cle API ou None si absente.
    """
    return keyring.get_password("elevenlabs_api_key", "telephonia")


def create_tts_provider(voice: str = "fr-FR-DeniseNeural") -> TTSProvider:
    """Selectionne automatiquement le provider TTS.

    Si une cle ElevenLabs est configuree dans le trousseau, utilise ElevenLabs.
    Sinon, utilise Edge TTS (gratuit).

    Args:
        voice: Voix Edge TTS a utiliser si ElevenLabs n'est pas disponible.

    Returns:
        Instance du provider TTS selectionne.
    """
    api_key = get_elevenlabs_key()
    if api_key:
        logger.info("Provider TTS : ElevenLabs")
        return ElevenLabsProvider(api_key=api_key)

    logger.info("Provider TTS : EdgeTTS (gratuit)")
    return EdgeTTSProvider(voice=voice)
