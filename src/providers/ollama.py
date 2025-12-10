"""
Ollama Provider

Implementation for Ollama local LLM inference engine.
"""

import httpx
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.providers.base import LLMProvider, ProviderStatus, ProviderType
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Models known to support tool calling in Ollama
OLLAMA_TOOL_CAPABLE_MODELS = [
    "qwen2.5",
    "qwen2",
    "llama3.1",
    "llama3.2",
    "llama3.3",
    "mistral",
    "mixtral",
    "command-r",
    "firefunction",
    "hermes",
    "nous-hermes",
]


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider.

    Uses Ollama's OpenAI-compatible API endpoint for inference.
    Default endpoint: http://localhost:11434
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct",
        host: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        """
        Initialize Ollama provider.

        Args:
            model_name: Ollama model to use
            host: Ollama server URL
            timeout: Request timeout in seconds
        """
        self._model_name = model_name
        self._host = host.rstrip("/")
        self._timeout = timeout

        logger.debug(
            "ollama_provider_initialized",
            model=model_name,
            host=host,
        )

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.OLLAMA

    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name

    @property
    def endpoint(self) -> str:
        """Get the OpenAI-compatible API endpoint."""
        return f"{self._host}/v1"

    def get_model(self) -> OpenAIModel:
        """
        Get a Pydantic AI compatible model instance.

        Returns:
            OpenAIModel configured for Ollama
        """
        # Use OpenAIProvider with custom base_url for Ollama compatibility
        provider = OpenAIProvider(
            base_url=self.endpoint,
            api_key="ollama",  # Ollama doesn't validate API keys
        )
        return OpenAIModel(
            model_name=self._model_name,
            provider=provider,
        )

    async def check_connection(self) -> ProviderStatus:
        """
        Check if Ollama is available and the model is loaded.

        Returns:
            ProviderStatus with connection details
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Check Ollama is running
                response = await client.get(f"{self._host}/api/version")
                response.raise_for_status()
                version_data = response.json()
                version = version_data.get("version", "unknown")

                # Check if model is available
                models_response = await client.get(f"{self._host}/api/tags")
                models_response.raise_for_status()
                models_data = models_response.json()

                available_models = [m.get("name", "") for m in models_data.get("models", [])]

                # Check if our model is in the list
                model_found = any(
                    self._model_name in m or m.startswith(self._model_name.split(":")[0])
                    for m in available_models
                )

                if not model_found:
                    return ProviderStatus(
                        available=False,
                        provider_type=self.provider_type,
                        model_name=self._model_name,
                        endpoint=self._host,
                        version=version,
                        error=f"Model '{self._model_name}' not found. Run: ollama pull {self._model_name}",
                    )

                return ProviderStatus(
                    available=True,
                    provider_type=self.provider_type,
                    model_name=self._model_name,
                    endpoint=self._host,
                    version=version,
                )

        except httpx.ConnectError:
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._host,
                error="Cannot connect to Ollama. Is it running?",
            )
        except Exception as e:
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._host,
                error=str(e),
            )

    async def list_models(self) -> list[str]:
        """
        List available models from Ollama.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self._host}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.error("ollama_list_models_error", error=str(e))
            return []

    def supports_tool_calling(self) -> bool:
        """
        Check if the configured model supports tool calling.

        Returns:
            True if tool calling is supported
        """
        model_lower = self._model_name.lower()
        return any(model in model_lower for model in OLLAMA_TOOL_CAPABLE_MODELS)
