"""Tests pour le module tts."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from telephonia.tts import (
    ElevenLabsTTS,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    TTSError,
    VoiceNotFoundError,
)


@pytest.fixture
def tts():
    return ElevenLabsTTS(api_key="test-key", voice_id="test-voice-id", base_delay=0.0)


class TestElevenLabsTTS:
    """Tests pour le client ElevenLabs."""

    def test_init(self, tts):
        assert tts.api_key == "test-key"
        assert tts.voice_id == "test-voice-id"
        assert tts.model == "eleven_multilingual_v2"

    def test_init_custom_model(self):
        client = ElevenLabsTTS(api_key="key", voice_id="vid", model="custom_model")
        assert client.model == "custom_model"

    @patch("telephonia.tts.requests.post")
    def test_synthesize_success(self, mock_post, tts):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake-mp3-audio-data"
        mock_post.return_value = mock_response

        result = tts.synthesize("Bonjour")

        assert result == b"fake-mp3-audio-data"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "test-voice-id" in call_kwargs[0][0]
        assert call_kwargs[1]["json"]["text"] == "Bonjour"

    @patch("telephonia.tts.requests.post")
    def test_synthesize_rate_limit(self, mock_post, tts):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with pytest.raises(RateLimitError, match="Rate limit"):
            tts.synthesize("Bonjour")

    @patch("telephonia.tts.requests.post")
    def test_synthesize_quota_exceeded(self, mock_post, tts):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with pytest.raises(QuotaExceededError, match="quota"):
            tts.synthesize("Bonjour")

    @patch("telephonia.tts.requests.post")
    def test_synthesize_voice_not_found(self, mock_post, tts):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        with pytest.raises(VoiceNotFoundError, match="introuvable"):
            tts.synthesize("Bonjour")

    @patch("telephonia.tts.requests.post")
    def test_synthesize_other_error(self, mock_post, tts):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(TTSError, match="500"):
            tts.synthesize("Bonjour")

    @patch("telephonia.tts.requests.get")
    def test_list_voices_success(self, mock_get, tts):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {"voice_id": "v1", "name": "Charlotte"},
                {"voice_id": "v2", "name": "Mathieu"},
            ]
        }
        mock_get.return_value = mock_response

        voices = tts.list_voices()

        assert len(voices) == 2
        assert voices[0]["name"] == "Charlotte"

    @patch("telephonia.tts.requests.get")
    def test_list_voices_error(self, mock_get, tts):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error"
        mock_get.return_value = mock_response

        with pytest.raises(TTSError):
            tts.list_voices()

    @patch("telephonia.tts.requests.post")
    def test_synthesize_connection_error(self, mock_post, tts):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(NetworkError, match="Connexion au serveur ElevenLabs"):
            tts.synthesize("Bonjour")

    @patch("telephonia.tts.requests.post")
    def test_synthesize_timeout(self, mock_post, tts):
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(NetworkError, match="Timeout"):
            tts.synthesize("Bonjour")

    def test_headers(self, tts):
        headers = tts._headers()
        assert headers["xi-api-key"] == "test-key"
        assert "Content-Type" in headers
