"""
Tests for LLM Providers

Tests for Ollama, Foundry Local, and provider factory.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.providers import LLMProvider, ProviderType, create_provider, get_available_providers
from src.providers.ollama import OllamaProvider
from src.providers.foundry import FoundryLocalProvider


@pytest.mark.unit
class TestProviderType:
    """Tests for ProviderType enum."""

    def test_ollama_type(self):
        """Test Ollama provider type."""
        assert ProviderType.OLLAMA.value == "ollama"

    def test_foundry_type(self):
        """Test Foundry Local provider type."""
        assert ProviderType.FOUNDRY_LOCAL.value == "foundry_local"

    def test_from_string(self):
        """Test creating ProviderType from string."""
        assert ProviderType("ollama") == ProviderType.OLLAMA
        assert ProviderType("foundry_local") == ProviderType.FOUNDRY_LOCAL


@pytest.mark.unit
class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_init_default(self):
        """Test default initialization."""
        provider = OllamaProvider()

        assert provider.provider_type == ProviderType.OLLAMA
        assert "localhost" in provider.endpoint

    def test_init_custom(self):
        """Test custom initialization."""
        provider = OllamaProvider(
            model_name="llama3.1:8b",
            host="http://custom:11434",
        )

        assert provider.model_name == "llama3.1:8b"
        assert provider.endpoint == "http://custom:11434"

    def test_get_model(self):
        """Test getting OpenAI-compatible model."""
        provider = OllamaProvider()
        model = provider.get_model()

        assert model is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_check_connection_success(self, mock_get):
        """Test successful connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.3.0"}
        mock_get.return_value = mock_response

        provider = OllamaProvider()
        status = await provider.check_connection()

        assert status.available is True
        assert status.version == "0.3.0"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_check_connection_failure(self, mock_get):
        """Test failed connection check."""
        mock_get.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        status = await provider.check_connection()

        assert status.available is False
        assert "Connection refused" in status.error

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_list_models(self, mock_get):
        """Test listing available models."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:7b-instruct"},
                {"name": "llama3.1:8b"},
            ]
        }
        mock_get.return_value = mock_response

        provider = OllamaProvider()
        models = await provider.list_models()

        assert "qwen2.5:7b-instruct" in models
        assert "llama3.1:8b" in models


@pytest.mark.unit
class TestFoundryLocalProvider:
    """Tests for Foundry Local provider."""

    def test_init_default(self):
        """Test default initialization."""
        provider = FoundryLocalProvider()

        assert provider.provider_type == ProviderType.FOUNDRY_LOCAL
        assert "127.0.0.1:55588" in provider.endpoint

    def test_init_custom(self):
        """Test custom initialization."""
        provider = FoundryLocalProvider(
            model_name="phi-3-mini",
            endpoint="http://custom:55588",
            api_key="test-key",
        )

        assert provider.model_name == "phi-3-mini"
        assert provider.endpoint == "http://custom:55588"

    def test_get_model(self):
        """Test getting OpenAI-compatible model."""
        provider = FoundryLocalProvider()
        model = provider.get_model()

        assert model is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_check_connection_success(self, mock_get):
        """Test successful connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"id": "phi-4"}]}
        mock_get.return_value = mock_response

        provider = FoundryLocalProvider()
        status = await provider.check_connection()

        assert status.available is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_check_connection_failure(self, mock_get):
        """Test failed connection check."""
        mock_get.side_effect = Exception("Connection refused")

        provider = FoundryLocalProvider()
        status = await provider.check_connection()

        assert status.available is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_list_models(self, mock_get):
        """Test listing available models."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "phi-4"},
                {"id": "phi-3-mini"},
            ]
        }
        mock_get.return_value = mock_response

        provider = FoundryLocalProvider()
        models = await provider.list_models()

        assert "phi-4" in models
        assert "phi-3-mini" in models


@pytest.mark.unit
class TestProviderFactory:
    """Tests for provider factory functions."""

    def test_create_provider_ollama(self):
        """Test creating Ollama provider via factory."""
        provider = create_provider(provider_type="ollama")

        assert isinstance(provider, OllamaProvider)
        assert provider.provider_type == ProviderType.OLLAMA

    def test_create_provider_foundry(self):
        """Test creating Foundry Local provider via factory."""
        provider = create_provider(provider_type="foundry_local")

        assert isinstance(provider, FoundryLocalProvider)
        assert provider.provider_type == ProviderType.FOUNDRY_LOCAL

    def test_create_provider_with_model(self):
        """Test creating provider with specific model."""
        provider = create_provider(
            provider_type="ollama",
            model_name="llama3.1:8b",
        )

        assert provider.model_name == "llama3.1:8b"

    def test_create_provider_default_from_settings(self):
        """Test creating provider using default settings."""
        with patch("src.providers.factory.settings") as mock_settings:
            mock_settings.llm_provider = "ollama"
            mock_settings.ollama_host = "http://localhost:11434"
            mock_settings.ollama_model = "qwen2.5:7b-instruct"

            provider = create_provider()

            assert isinstance(provider, OllamaProvider)

    def test_create_provider_invalid_type(self):
        """Test creating provider with invalid type."""
        with pytest.raises(ValueError):
            create_provider(provider_type="invalid")

    @pytest.mark.asyncio
    @patch("src.providers.ollama.OllamaProvider.check_connection")
    @patch("src.providers.foundry.FoundryLocalProvider.check_connection")
    async def test_get_available_providers(self, mock_foundry_check, mock_ollama_check):
        """Test getting status of all providers."""
        # Setup mocks
        ollama_status = MagicMock()
        ollama_status.available = True
        ollama_status.provider_type = ProviderType.OLLAMA
        mock_ollama_check.return_value = ollama_status

        foundry_status = MagicMock()
        foundry_status.available = False
        foundry_status.provider_type = ProviderType.FOUNDRY_LOCAL
        mock_foundry_check.return_value = foundry_status

        statuses = await get_available_providers()

        assert len(statuses) == 2


@pytest.mark.integration
class TestProviderIntegration:
    """Integration tests for providers."""

    @pytest.mark.requires_ollama
    @pytest.mark.asyncio
    async def test_ollama_real_connection(self):
        """Test real Ollama connection (requires running Ollama)."""
        provider = OllamaProvider()
        status = await provider.check_connection()

        # This will pass if Ollama is running, skip otherwise
        if not status.available:
            pytest.skip("Ollama not available")

        assert status.available is True
        models = await provider.list_models()
        assert isinstance(models, list)

    @pytest.mark.requires_foundry
    @pytest.mark.asyncio
    async def test_foundry_real_connection(self):
        """Test real Foundry Local connection (requires running instance)."""
        provider = FoundryLocalProvider()
        status = await provider.check_connection()

        # This will pass if Foundry Local is running, skip otherwise
        if not status.available:
            pytest.skip("Foundry Local not available")

        assert status.available is True


@pytest.mark.unit
class TestProviderAbstraction:
    """Tests for provider abstraction."""

    def test_ollama_is_llm_provider(self):
        """Test Ollama provider implements LLMProvider."""
        provider = OllamaProvider()
        assert isinstance(provider, LLMProvider)

    def test_foundry_is_llm_provider(self):
        """Test Foundry provider implements LLMProvider."""
        provider = FoundryLocalProvider()
        assert isinstance(provider, LLMProvider)

    def test_providers_have_same_interface(self):
        """Test both providers have the same interface."""
        ollama = OllamaProvider()
        foundry = FoundryLocalProvider()

        # Both should have these attributes/methods
        assert hasattr(ollama, "provider_type")
        assert hasattr(ollama, "model_name")
        assert hasattr(ollama, "endpoint")
        assert hasattr(ollama, "get_model")
        assert hasattr(ollama, "check_connection")
        assert hasattr(ollama, "list_models")

        assert hasattr(foundry, "provider_type")
        assert hasattr(foundry, "model_name")
        assert hasattr(foundry, "endpoint")
        assert hasattr(foundry, "get_model")
        assert hasattr(foundry, "check_connection")
        assert hasattr(foundry, "list_models")
