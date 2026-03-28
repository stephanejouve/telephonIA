"""Tests pour le retry avec backoff exponentiel d'ElevenLabs."""

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
    return ElevenLabsTTS(
        api_key="test-key", voice_id="test-voice-id", max_retries=2, base_delay=0.0
    )


def _mock_response(status_code, content=b"", text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.text = text
    return resp


class TestRetryThenSuccess:
    """Tests pour les scenarios retry puis succes."""

    @patch("telephonia.tts.requests.post")
    def test_retry_then_success(self, mock_post, tts):
        """429 puis 200 → retourne audio, 2 appels."""
        mock_post.side_effect = [
            _mock_response(429),
            _mock_response(200, content=b"audio-data"),
        ]
        result = tts.synthesize("Bonjour")
        assert result == b"audio-data"
        assert mock_post.call_count == 2

    @patch("telephonia.tts.requests.post")
    def test_connection_error_then_success(self, mock_post, tts):
        """ConnectionError puis 200 → OK."""
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            _mock_response(200, content=b"audio-data"),
        ]
        result = tts.synthesize("Bonjour")
        assert result == b"audio-data"
        assert mock_post.call_count == 2

    @patch("telephonia.tts.requests.post")
    def test_timeout_then_success(self, mock_post, tts):
        """Timeout puis 200 → OK."""
        mock_post.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            _mock_response(200, content=b"audio-data"),
        ]
        result = tts.synthesize("Bonjour")
        assert result == b"audio-data"
        assert mock_post.call_count == 2


class TestRetryExhausted:
    """Tests pour l'epuisement des tentatives."""

    @patch("telephonia.tts.requests.post")
    def test_retry_exhausted(self, mock_post, tts):
        """429 x3 → RateLimitError, 3 appels."""
        mock_post.return_value = _mock_response(429)
        with pytest.raises(RateLimitError):
            tts.synthesize("Bonjour")
        assert mock_post.call_count == 3  # 1 + 2 retries

    @patch("telephonia.tts.requests.post")
    def test_network_error_exhausted(self, mock_post, tts):
        """ConnectionError x3 → NetworkError."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with pytest.raises(NetworkError):
            tts.synthesize("Bonjour")
        assert mock_post.call_count == 3


class TestNoRetryErrors:
    """Tests pour les erreurs non retentees (echec immediat)."""

    @patch("telephonia.tts.requests.post")
    def test_quota_exceeded_no_retry(self, mock_post, tts):
        """401 → immediat, 1 appel."""
        mock_post.return_value = _mock_response(401)
        with pytest.raises(QuotaExceededError):
            tts.synthesize("Bonjour")
        assert mock_post.call_count == 1

    @patch("telephonia.tts.requests.post")
    def test_voice_not_found_no_retry(self, mock_post, tts):
        """404 → immediat, 1 appel."""
        mock_post.return_value = _mock_response(404)
        with pytest.raises(VoiceNotFoundError):
            tts.synthesize("Bonjour")
        assert mock_post.call_count == 1

    @patch("telephonia.tts.requests.post")
    def test_server_error_no_retry(self, mock_post, tts):
        """500 → immediat, 1 appel."""
        mock_post.return_value = _mock_response(500, text="Internal Server Error")
        with pytest.raises(TTSError):
            tts.synthesize("Bonjour")
        assert mock_post.call_count == 1


class TestRetryConfig:
    """Tests pour la configuration retry."""

    def test_default_config(self):
        """Valeurs par defaut : max_retries=3, base_delay=1.0."""
        client = ElevenLabsTTS(api_key="key", voice_id="vid")
        assert client.max_retries == 3
        assert client.base_delay == 1.0

    @patch("telephonia.tts.requests.post")
    def test_no_retry_config(self, mock_post):
        """max_retries=0 → 1 seul appel."""
        client = ElevenLabsTTS(api_key="key", voice_id="vid", max_retries=0, base_delay=0.0)
        mock_post.return_value = _mock_response(429)
        with pytest.raises(RateLimitError):
            client.synthesize("Bonjour")
        assert mock_post.call_count == 1
