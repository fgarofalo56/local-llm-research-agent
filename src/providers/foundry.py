"""
Foundry Local Provider

Implementation for Microsoft Foundry Local AI inference runtime.
https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started
"""

import httpx
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.providers.base import LLMProvider, ProviderStatus, ProviderType
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default Foundry Local endpoint
# Note: Foundry Local SDK typically runs on dynamic ports, but 53760 is a common default
# The SDK's FoundryLocalManager will provide the actual endpoint when auto-start is used
FOUNDRY_DEFAULT_ENDPOINT = "http://127.0.0.1:53760"

# Models known to support tool calling in Foundry Local
# IMPORTANT: Only specific model variants support function calling!
# - phi-4-mini supports function calling (phi-4 does NOT)
# - phi-3.5-mini supports function calling
# See: https://github.com/microsoft/PhiCookBook/tree/main/md/02.Application/07.FunctionCalling
FOUNDRY_TOOL_CAPABLE_MODELS = [
    "phi-4-mini",      # Supports function calling
    "phi-3.5-mini",    # Supports function calling
    "phi-3-mini",      # Supports function calling
    "qwen2.5",         # Supports function calling
    "llama3.1",        # Supports function calling
    "llama3.2",        # Supports function calling
    "mistral-nemo",    # Supports function calling
]

# Models that do NOT support tool calling (common mistake)
FOUNDRY_NON_TOOL_MODELS = [
    "phi-4",           # Regular phi-4 does NOT support tools - use phi-4-mini
    "phi-4-multimodal", # Does NOT support tool calling
    "gpt-oss-20b",     # General purpose, no tool support
]


class FoundryLocalProvider(LLMProvider):
    """
    Microsoft Foundry Local LLM provider.

    Uses Foundry Local's OpenAI-compatible API endpoint for inference.
    Default endpoint: http://127.0.0.1:53760

    Foundry Local can be installed via:
        pip install foundry-local-sdk

    And started with:
        from foundry_local import FoundryLocalManager
        manager = FoundryLocalManager("model-alias")
    """

    def __init__(
        self,
        model_name: str | None = None,
        endpoint: str | None = None,
        api_key: str = "",
        timeout: int = 120,
        auto_start: bool | None = None,
    ):
        """
        Initialize Foundry Local provider.

        Args:
            model_name: Model alias to use (e.g., "phi-4", "mistral-7b")
            endpoint: Foundry Local API endpoint (default from settings or http://127.0.0.1:53760)
            api_key: API key (optional, not required for local usage)
            timeout: Request timeout in seconds
            auto_start: Whether to auto-start Foundry Local using SDK (default from settings)
        """
        self._model_name = (model_name or settings.foundry_model).strip()
        self._endpoint = (endpoint or settings.foundry_endpoint or FOUNDRY_DEFAULT_ENDPOINT).rstrip(
            "/"
        )
        self._api_key = api_key or "foundry-local"  # Placeholder for local usage
        self._timeout = timeout
        self._manager = None
        self._auto_start = auto_start if auto_start is not None else settings.foundry_auto_start
        self._actual_model_name: str | None = None  # The model name returned by the server

        logger.debug(
            "foundry_local_provider_initialized",
            model=self._model_name,
            endpoint=self._endpoint,
            auto_start=self._auto_start,
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
        # Use the actual model name from server if we've discovered it
        # If not discovered yet, try to resolve it synchronously
        if not self._actual_model_name:
            self._resolve_model_name_sync()

        model_to_use = self._actual_model_name or self._model_name

        # Use OpenAIProvider with custom base_url for Foundry Local compatibility
        provider = OpenAIProvider(
            base_url=self.endpoint,
            api_key=self._api_key,
        )

        logger.info(
            "foundry_get_model",
            model=model_to_use,
            endpoint=self.endpoint,
        )

        return OpenAIModel(
            model_name=model_to_use,
            provider=provider,
        )

    def _resolve_model_name_sync(self) -> None:
        """
        Synchronously resolve the actual model name from Foundry Local.

        This is called when get_model() is invoked before check_connection().
        """
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self._endpoint}/v1/models")
                response.raise_for_status()
                data = response.json()

                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                if not model_ids:
                    logger.warning("foundry_no_models_available")
                    return

                # Match model name (same logic as check_connection)
                model_lower = self._model_name.lower()

                # Exact match
                for m_id in model_ids:
                    if m_id.lower() == model_lower:
                        self._actual_model_name = m_id
                        logger.info("foundry_model_resolved", requested=self._model_name, actual=m_id)
                        return

                # Starts with
                for m_id in model_ids:
                    m_lower = m_id.lower()
                    if m_lower.startswith(model_lower) or m_lower.startswith(model_lower.replace("-", "")):
                        self._actual_model_name = m_id
                        logger.info("foundry_model_resolved", requested=self._model_name, actual=m_id)
                        return

                # Contains
                for m_id in model_ids:
                    if model_lower in m_id.lower():
                        self._actual_model_name = m_id
                        logger.info("foundry_model_resolved", requested=self._model_name, actual=m_id)
                        return

                # Use first available as fallback
                self._actual_model_name = model_ids[0]
                logger.warning(
                    "foundry_model_fallback",
                    requested=self._model_name,
                    using=model_ids[0],
                    available=model_ids,
                )

        except Exception as e:
            logger.warning("foundry_model_resolve_error", error=str(e))

    async def check_connection(self) -> ProviderStatus:
        """
        Check if Foundry Local is available and optionally auto-start it.

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

                logger.debug(
                    "foundry_models_response",
                    models=model_ids,
                    requested_model=self._model_name,
                )

                # Find a matching model - check for exact match first, then partial
                matched_model = None
                model_lower = self._model_name.lower()

                # First pass: exact match
                for m_id in model_ids:
                    if m_id.lower() == model_lower:
                        matched_model = m_id
                        break

                # Second pass: starts with the requested model (e.g., "Phi-4" matches "Phi-4-cuda-gpu:0")
                if not matched_model:
                    for m_id in model_ids:
                        m_lower = m_id.lower()
                        # Check if model ID starts with our requested model name
                        if m_lower.startswith(model_lower) or m_lower.startswith(
                            model_lower.replace("-", "")
                        ):
                            matched_model = m_id
                            break

                # Third pass: requested model is contained in available model ID
                if not matched_model:
                    for m_id in model_ids:
                        m_lower = m_id.lower()
                        if model_lower in m_lower:
                            matched_model = m_id
                            break

                if matched_model:
                    # Store the actual model name for use in get_model()
                    self._actual_model_name = matched_model
                    logger.info(
                        "foundry_model_matched",
                        requested=self._model_name,
                        actual=matched_model,
                    )
                    return ProviderStatus(
                        available=True,
                        provider_type=self.provider_type,
                        model_name=matched_model,
                        endpoint=self._endpoint,
                    )

                if model_ids:
                    # Model not found but Foundry is running - use first available
                    self._actual_model_name = model_ids[0]
                    logger.warning(
                        "foundry_model_not_found",
                        requested=self._model_name,
                        using=model_ids[0],
                        available=model_ids,
                    )
                    return ProviderStatus(
                        available=True,
                        provider_type=self.provider_type,
                        model_name=model_ids[0],
                        endpoint=self._endpoint,
                        error=f"Requested model '{self._model_name}' not loaded. Using: {model_ids[0]}",
                    )

                return ProviderStatus(
                    available=False,
                    provider_type=self.provider_type,
                    model_name=self._model_name,
                    endpoint=self._endpoint,
                    error="No models loaded in Foundry Local",
                )

        except httpx.ConnectError:
            # Try auto-start if enabled
            if self._auto_start:
                return await self._try_auto_start()

            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error=(
                    f"Cannot connect to Foundry Local at {self._endpoint}. "
                    "Start it with: 'foundry model run phi-4' or set FOUNDRY_AUTO_START=true in .env"
                ),
            )
        except Exception as e:
            logger.error("foundry_check_connection_error", error=str(e))
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error=str(e),
            )

    async def _try_auto_start(self) -> ProviderStatus:
        """Try to auto-start Foundry Local using the SDK."""
        try:
            from foundry_local import FoundryLocalManager

            logger.info(
                "foundry_auto_starting",
                model=self._model_name,
            )

            # Start Foundry Local with the specified model
            self._manager = FoundryLocalManager(self._model_name)

            # Update endpoint and API key from manager
            self._endpoint = self._manager.endpoint.rstrip("/")
            self._api_key = self._manager.api_key

            logger.info(
                "foundry_auto_started",
                model=self._model_name,
                endpoint=self._endpoint,
            )

            # Re-check connection now that it's started
            return await self.check_connection()

        except ImportError:
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error=(
                    "foundry-local-sdk not installed. Install with: "
                    "'uv sync --extra foundry' or 'pip install foundry-local-sdk'"
                ),
            )
        except Exception as e:
            logger.error("foundry_auto_start_error", error=str(e))
            return ProviderStatus(
                available=False,
                provider_type=self.provider_type,
                model_name=self._model_name,
                endpoint=self._endpoint,
                error=f"Failed to auto-start Foundry Local: {e}",
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

        IMPORTANT: Only specific model variants support function calling in Foundry Local!
        - phi-4-mini: YES (supports function calling)
        - phi-4: NO (does NOT support function calling)
        - phi-4-multimodal: NO (does NOT support function calling)

        Returns:
            True if tool calling is supported
        """
        model_lower = self._model_name.lower()

        # First check if it's explicitly a non-tool model
        for non_tool_model in FOUNDRY_NON_TOOL_MODELS:
            if non_tool_model.lower() in model_lower:
                # But make sure it's not actually a tool-capable variant
                # e.g., "phi-4-mini" contains "phi-4" but IS tool capable
                is_tool_capable = any(
                    tool_model.lower() in model_lower
                    for tool_model in FOUNDRY_TOOL_CAPABLE_MODELS
                )
                if not is_tool_capable:
                    return False

        # Check if it matches a known tool-capable model
        return any(model.lower() in model_lower for model in FOUNDRY_TOOL_CAPABLE_MODELS)

    def get_tool_calling_warning(self) -> str | None:
        """
        Get a warning message if the model doesn't support tool calling.

        Returns:
            Warning message string, or None if model supports tools
        """
        if self.supports_tool_calling():
            return None

        model_lower = self._model_name.lower()

        # Check for common mistakes
        if "phi-4" in model_lower and "mini" not in model_lower:
            return (
                f"Model '{self._model_name}' does NOT support tool calling. "
                "The regular Phi-4 model cannot use MCP tools. "
                "Use 'phi-4-mini' instead which supports function calling. "
                "Run: foundry model run phi-4-mini"
            )

        if "phi-4-multimodal" in model_lower:
            return (
                f"Model '{self._model_name}' does NOT support tool calling. "
                "Phi-4-multimodal is for vision tasks, not function calling. "
                "Use 'phi-4-mini' instead for MCP tools."
            )

        return (
            f"Model '{self._model_name}' may not support tool calling. "
            "For MCP tool support, use phi-4-mini, qwen2.5, or llama3.1/3.2. "
            "The model may describe tools instead of calling them."
        )

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
