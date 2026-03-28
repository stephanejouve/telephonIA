"""Client ElevenLabs Text-to-Speech."""

import requests


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


class ElevenLabsTTS:
    """Client pour l'API ElevenLabs Text-to-Speech.

    Args:
        api_key: Cle API ElevenLabs.
        voice_id: Identifiant de la voix a utiliser.
        model: Modele TTS (defaut: eleven_multilingual_v2).
    """

    BASE_URL = "https://api.elevenlabs.io"

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model: str = "eleven_multilingual_v2",
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model

    def _headers(self) -> dict:
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def synthesize(self, text: str) -> bytes:
        """Synthetise du texte en audio MP3.

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
