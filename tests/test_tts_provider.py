"""Tests pour le module tts_provider."""

import io
from unittest.mock import MagicMock, patch

import pytest
from pydub.generators import Sine

from telephonia.tts import NetworkError
from telephonia.tts_provider import (
    EdgeTTSProvider,
    ElevenLabsProvider,
    TTSProvider,
    create_tts_provider,
    get_elevenlabs_key,
)


@pytest.fixture
def fake_mp3_bytes():
    """Audio synthetique en MP3."""
    tone = Sine(440).to_audio_segment(duration=1000)
    buffer = io.BytesIO()
    tone.export(buffer, format="mp3")
    return buffer.getvalue()


class TestTTSProviderInterface:
    """Tests pour l'interface abstraite."""

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            TTSProvider()

    def test_elevenlabs_is_provider(self):
        provider = ElevenLabsProvider(api_key="test-key")
        assert isinstance(provider, TTSProvider)

    def test_edge_tts_is_provider(self):
        provider = EdgeTTSProvider()
        assert isinstance(provider, TTSProvider)


class TestElevenLabsProvider:
    """Tests pour ElevenLabsProvider."""

    @patch("telephonia.tts.requests.post")
    def test_synthesize_returns_bytes(self, mock_post, fake_mp3_bytes):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_mp3_bytes
        mock_post.return_value = mock_response

        provider = ElevenLabsProvider(api_key="test-key")
        result = provider.synthesize("Bonjour")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_voice_format_is_mp3(self):
        provider = ElevenLabsProvider(api_key="test-key")
        assert provider.voice_format == "mp3"

    def test_default_voice_id(self):
        provider = ElevenLabsProvider(api_key="test-key")
        assert provider.client.voice_id == "XB0fDUnXU5powFXDhCwa"

    def test_custom_voice_id(self):
        provider = ElevenLabsProvider(api_key="test-key", voice_id="custom-id")
        assert provider.client.voice_id == "custom-id"


class TestEdgeTTSProvider:
    """Tests pour EdgeTTSProvider."""

    def test_default_voice(self):
        provider = EdgeTTSProvider()
        assert provider.voice == "fr-FR-DeniseNeural"

    def test_custom_voice(self):
        provider = EdgeTTSProvider(voice="fr-FR-HenriNeural")
        assert provider.voice == "fr-FR-HenriNeural"

    def test_voice_format_is_mp3(self):
        provider = EdgeTTSProvider()
        assert provider.voice_format == "mp3"

    @patch("telephonia.tts_provider.edge_tts")
    def test_synthesize_returns_bytes(self, mock_edge_tts, fake_mp3_bytes):
        # Simuler le stream async
        async def fake_stream():
            yield {"type": "audio", "data": fake_mp3_bytes[:100]}
            yield {"type": "WordBoundary", "text": "Bonjour", "offset": 0, "duration": 0.5}
            yield {"type": "audio", "data": fake_mp3_bytes[100:]}

        mock_communicate = MagicMock()
        mock_communicate.stream = fake_stream
        mock_edge_tts.Communicate.return_value = mock_communicate

        provider = EdgeTTSProvider()
        result = provider.synthesize("Bonjour")

        assert isinstance(result, bytes)
        assert result == fake_mp3_bytes
        mock_edge_tts.Communicate.assert_called_once_with("Bonjour", voice="fr-FR-DeniseNeural")

    @patch("telephonia.tts_provider.edge_tts")
    def test_synthesize_network_error(self, mock_edge_tts):
        """Erreur reseau Edge TTS → NetworkError."""
        mock_edge_tts.Communicate.side_effect = Exception("Connection failed")

        provider = EdgeTTSProvider()
        with pytest.raises(NetworkError, match="reseau ou service indisponible"):
            provider.synthesize("Bonjour")

    @patch("telephonia.tts_provider.edge_tts")
    def test_synthesize_empty_audio_raises(self, mock_edge_tts):
        async def empty_stream():
            yield {"type": "WordBoundary", "text": "Bonjour", "offset": 0, "duration": 0.5}

        mock_communicate = MagicMock()
        mock_communicate.stream = empty_stream
        mock_edge_tts.Communicate.return_value = mock_communicate

        provider = EdgeTTSProvider()
        with pytest.raises(Exception, match="aucun audio"):
            provider.synthesize("Bonjour")


class TestSynthesizeBatch:
    """Tests pour synthesize_batch."""

    def test_synthesize_batch_default(self, fake_mp3_bytes):
        """Le provider de base appelle synthesize() N fois."""

        class FakeProvider(TTSProvider):
            def synthesize(self, text: str) -> bytes:
                return fake_mp3_bytes

        provider = FakeProvider()
        results = provider.synthesize_batch(["Un", "Deux", "Trois"])

        assert len(results) == 3
        assert all(r == fake_mp3_bytes for r in results)

    @patch("telephonia.tts_provider.edge_tts")
    def test_edge_tts_synthesize_batch(self, mock_edge_tts, fake_mp3_bytes):
        """EdgeTTS batch → un seul asyncio.run(), N resultats."""
        call_count = 0

        async def fake_stream():
            nonlocal call_count
            call_count += 1
            yield {"type": "audio", "data": fake_mp3_bytes}

        mock_communicate = MagicMock()
        mock_communicate.stream = fake_stream
        mock_edge_tts.Communicate.return_value = mock_communicate

        provider = EdgeTTSProvider()
        results = provider.synthesize_batch(["Un", "Deux", "Trois"])

        assert len(results) == 3
        assert all(isinstance(r, bytes) for r in results)
        assert mock_edge_tts.Communicate.call_count == 3

    @patch("telephonia.tts_provider.edge_tts")
    def test_edge_tts_synthesize_batch_partial_failure(self, mock_edge_tts, fake_mp3_bytes):
        """EdgeTTS batch avec return_exceptions — erreur partielle."""
        call_index = 0

        def make_communicate(text, voice):
            nonlocal call_index
            idx = call_index
            call_index += 1
            comm = MagicMock()
            if idx == 1:
                # Deuxieme appel echoue
                async def failing_stream():
                    raise Exception("Service indisponible")
                    yield  # noqa: F811 - necessaire pour en faire un async generator

                comm.stream = failing_stream
            else:

                async def ok_stream():
                    yield {"type": "audio", "data": fake_mp3_bytes}

                comm.stream = ok_stream
            return comm

        mock_edge_tts.Communicate.side_effect = make_communicate

        provider = EdgeTTSProvider()
        results = provider.synthesize_batch(["Un", "Deux", "Trois"])

        assert len(results) == 3
        assert isinstance(results[0], bytes)
        assert isinstance(results[1], Exception)
        assert isinstance(results[2], bytes)


class TestProviderSelection:
    """Tests pour la selection automatique du provider."""

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_selection_with_key_returns_elevenlabs(self, mock_get):
        mock_get.return_value = "my-elevenlabs-key"
        provider = create_tts_provider()
        assert isinstance(provider, ElevenLabsProvider)
        mock_get.assert_called_once_with("elevenlabs_api_key", "telephonia")

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_selection_no_key_returns_edge(self, mock_get):
        mock_get.return_value = None
        provider = create_tts_provider()
        assert isinstance(provider, EdgeTTSProvider)

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_selection_no_key_uses_default_voice(self, mock_get):
        mock_get.return_value = None
        provider = create_tts_provider()
        assert provider.voice == "fr-FR-DeniseNeural"

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_selection_no_key_custom_voice(self, mock_get):
        mock_get.return_value = None
        provider = create_tts_provider(voice="fr-FR-HenriNeural")
        assert provider.voice == "fr-FR-HenriNeural"

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_get_elevenlabs_key_found(self, mock_get):
        mock_get.return_value = "secret-key"
        assert get_elevenlabs_key() == "secret-key"

    @patch("telephonia.tts_provider.keyring.get_password")
    def test_get_elevenlabs_key_not_found(self, mock_get):
        mock_get.return_value = None
        assert get_elevenlabs_key() is None
