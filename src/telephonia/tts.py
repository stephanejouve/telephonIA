"""Client ElevenLabs Text-to-Speech."""

import logging
import random
import time

import requests

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Erreur lors de la synthese vocale."""


class RateLimitError(TTSError):
    """Rate limit atteint (429)."""


class QuotaExceededError(TTSError):
    """Quota depasse ou cle API invalide (401)."""


class VoiceNotFoundError(TTSError):
    """Voix introuvable (404)."""


class NetworkError(TTSError):
    """Erreur reseau (connexion, timeout)."""


_RETRYABLE = (RateLimitError, NetworkError)


class ElevenLabsTTS:
    """Client pour l'API ElevenLabs Text-to-Speech.

    Args:
        api_key: Cle API ElevenLabs.
        voice_id: Identifiant de la voix a utiliser.
        model: Modele TTS (defaut: eleven_multilingual_v2).
        max_retries: Nombre maximum de tentatives apres echec (defaut: 3).
        base_delay: Delai de base en secondes pour le backoff exponentiel (defaut: 1.0).
    """

    BASE_URL = "https://api.elevenlabs.io"

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model: str = "eleven_multilingual_v2",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _headers(self) -> dict:
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _call_api(self, text: str) -> bytes:
        """Appel HTTP a l'API ElevenLabs (sans retry).

        Args:
            text: Texte a convertir en voix.

        Returns:
            Contenu audio MP3 en bytes.

        Raises:
            NetworkError: Si la connexion echoue ou timeout.
            RateLimitError: Si le rate limit est atteint (429).
            QuotaExceededError: Si le quota est depasse (401).
            VoiceNotFoundError: Si la voix est introuvable (404).
            TTSError: Pour toute autre erreur API.
        """
        url = f"{self.BASE_URL}/v1/text-to-speech/{self.voice_id}"
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(
                "Connexion au serveur ElevenLabs impossible. Verifiez votre connexion."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise NetworkError("Timeout lors de l'appel a ElevenLabs.") from exc

        if response.status_code == 429:
            raise RateLimitError("Rate limit atteint. Reessayez plus tard.")
        if response.status_code == 401:
            raise QuotaExceededError("Cle API invalide ou quota depasse.")
        if response.status_code == 404:
            raise VoiceNotFoundError(f"Voix '{self.voice_id}' introuvable.")
        if response.status_code != 200:
            raise TTSError(f"Erreur API ElevenLabs: {response.status_code} - {response.text}")

        return response.content

    def synthesize(self, text: str) -> bytes:
        """Synthetise du texte en audio MP3 avec retry sur erreurs transitoires.

        Retente automatiquement sur RateLimitError et NetworkError avec
        backoff exponentiel + jitter. Les autres erreurs echouent immediatement.

        Args:
            text: Texte a convertir en voix.

        Returns:
            Contenu audio MP3 en bytes.

        Raises:
            NetworkError: Si la connexion echoue apres toutes les tentatives.
            RateLimitError: Si le rate limit persiste apres toutes les tentatives.
            QuotaExceededError: Si le quota est depasse (401).
            VoiceNotFoundError: Si la voix est introuvable (404).
            TTSError: Pour toute autre erreur API.
        """
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._call_api(text)
            except _RETRYABLE as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt) + random.uniform(
                        0, self.base_delay * 0.5
                    )
                    logger.warning(
                        "Tentative %d/%d echouee (%s), retry dans %.1fs",
                        attempt + 1,
                        self.max_retries + 1,
                        type(exc).__name__,
                        delay,
                    )
                    time.sleep(delay)
        raise last_error

    def list_voices(self) -> list[dict]:
        """Liste les voix disponibles.

        Returns:
            Liste de dictionnaires avec les infos de chaque voix.

        Raises:
            TTSError: En cas d'erreur API.
        """
        url = f"{self.BASE_URL}/v1/voices"
        response = requests.get(url, headers=self._headers(), timeout=30)

        if response.status_code != 200:
            raise TTSError(f"Erreur API ElevenLabs: {response.status_code} - {response.text}")

        return response.json().get("voices", [])
