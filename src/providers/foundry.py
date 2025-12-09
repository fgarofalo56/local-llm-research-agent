"""
Foundry Local Provider

Implementation for Microsoft Foundry Local AI inference runtime.
https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started
"""

import httpx
from pydantic_ai.models.openai import OpenAIModel

from src.providers.base import LLMProvider, ProviderStatus, ProviderType
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default Foundry Local endpoint
FOUNDRY_DEFAULT_ENDPOINT = "http://127.0.0.1:55588"

# Models known to support tool calling in Foundry Local
FOUNDRY_TOOL_CAPABLE_MODELS = [
    "phi-4",
    "phi-3",
    "mistral",
    "llama",
    "qwen",
]


class FoundryLocalProvider(LLMProvider):
    """
    Microsoft Foundry Local LLM provider.

    Uses Foundry Local's OpenAI-compatible API endpoint for inference.
    Default endpoint: http://127.0.0.1:55588

    Foundry Local can be installed via:
        pip install foundry-local-sdk

    And started with:
        from foundry_local import FoundryLocalManager
        manager = FoundryLocalManager("model-alias")
    """

    def __init__(
        self,
        model_name: str = "phi-4",
        endpoint: str | None = None,
        api_key: str = "",
        timeout: int = 120,
    ):
        """
        Initialize Foundry Local provider.

        Args:
            model_name: Model alias to use (e.g., "phi-4", "mistral-7b")
            endpoint: Foundry Local API endpoint (default: http://127.0.0.1:55588)
            api_key: API key (optional, not required for local usage)
            timeout: Request timeout in seconds
        """
        self._model_name = model_name
        self._endpoint = (endpoint or FOUNDRY_DEFAULT_ENDPOINT).rstrip("/")
        self._api_key = api_key or "foundry-local"  # Placeholder for local usage
        self._timeout = timeout
        self._manager = None

        logger.debug(
            "foundry_local_provider_initialized",
            model=model_name,
            endpoint=self._endpoint,
        )

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.FOUNDRY_LOCAL

    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name

    @property
    def endpoint(self) -> str:
        """Get the OpenAI-compatible API endpoint."""
        return f"{self._endpoint}/v1"

    def get_model(self) -> OpenAIModel:
        """
        Get a Pydantic AI compatible model instance.

        Returns:
            OpenAIModel configured for Foundry Local
        """
        return OpenAIModel(
            model_name=self._model_name,
            base_url=self.endpoint,
            api_key=self._api_key,
        )

    async def check_connection(self) -> ProviderStatus:
        """
        Check if Foundry Local is available.

        Returns:
            ProviderStatus with connection details
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try to get models list (OpenAI-compatible endpoint)
                response = await client.get(f"{self._endpoint}/v1/models")
                response.raise_for_status()
                data = response.json()

                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                # Check if our model is loaded
                model_found = any(
                    self._model_name in m_id or m_id.startswith(self._model_name.split("-")[0])
                    for m_id in model_ids
                )

                if not model_found and model_ids:
                    # Model not found but Foundry is running
                    return ProviderStatus(
                        available=True,  # Foundry is available, just different model
                        provider_type=self.provider_type,
                        model_name=model_ids[0] if model_ids else self._model_name,
                        endpoint=self._endpoint,
                        error=f"Requested model '{self._model_name}' not loaded. Available: {model_ids}",
                    )

                return ProviderStatus(
                    available=True,
                    provider_type=self.provider_type,
                    model_name=self._model_name,
                    endpoint=self._endpoint,
                )

        except httpx.ConnectError:
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error="Cannot connect to Foundry Local. Start it with: foundry-local-sdk or FoundryLocalManager",
            )
        except Exception as e:
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error=str(e),
            )

    async def list_models(self) -> list[str]:
        """
        List available models from Foundry Local.

        Returns:
            List of model IDs
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self._endpoint}/v1/models")
                response.raise_for_status()
                data = response.json()
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception as e:
            logger.error("foundry_list_models_error", error=str(e))
            return []

    def supports_tool_calling(self) -> bool:
        """
        Check if the configured model supports tool calling.

        Returns:
            True if tool calling is supported
        """
        model_lower = self._model_name.lower()
        return any(model in model_lower for model in FOUNDRY_TOOL_CAPABLE_MODELS)

    @staticmethod
    def start_with_sdk(model_alias: str) -> "FoundryLocalProvider":
        """
        Start Foundry Local using the SDK and return a configured provider.

        This method requires foundry-local-sdk to be installed:
            pip install foundry-local-sdk

        Args:
            model_alias: Model alias (e.g., "phi-4", "qwen2.5-0.5b")

        Returns:
            FoundryLocalProvider configured with the running instance

        Raises:
            ImportError: If foundry-local-sdk is not installed
        """
        try:
            from foundry_local import FoundryLocalManager
        except ImportError as e:
            raise ImportError(
                "foundry-local-sdk is required for automatic Foundry Local startup. "
                "Install with: pip install foundry-local-sdk"
            ) from e

        # Start Foundry Local with the specified model
        manager = FoundryLocalManager(model_alias)

        # Create provider with manager's endpoint and API key
        provider = FoundryLocalProvider(
            model_name=model_alias,
            endpoint=manager.endpoint,
            api_key=manager.api_key,
        )
        provider._manager = manager

        logger.info(
            "foundry_local_started_with_sdk",
            model=model_alias,
            endpoint=manager.endpoint,
        )

        return provider
