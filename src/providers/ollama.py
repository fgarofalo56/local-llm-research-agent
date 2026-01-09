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
# Based on official Ollama documentation and modelfile templates
OLLAMA_TOOL_CAPABLE_MODELS = [
    # Qwen family - all versions support tool calling
    "qwen3",  # Latest - native tool calling support
    "qwen2.5",  # Strong tool calling support
    "qwen2",  # Tool calling support
    "qwen3-vl",  # Vision + tool calling
    # Llama family - 3.1+ versions support tool calling
    "llama3.1",  # Native tool calling
    "llama3.2",  # Native tool calling
    "llama3.3",  # Native tool calling
    "llama4",  # Latest - likely supports tools (needs verification per variant)
    # Mistral family
    "mistral",  # Tool calling support
    "mistral-nemo",  # Tool calling support
    "mixtral",  # MoE with tool calling
    # Command-R family - specialized for RAG + tools
    "command-r",  # Cohere's tool-optimized model
    "command-r-plus",  # Enhanced version
    # Phi family - check specific variants
    "phi3",  # Phi-3 supports tools
    "phi3.5",  # Phi-3.5 supports tools
    "phi4",  # Phi-4 supports tools (14b variant)
    # Gemma family
    "gemma2",  # Tool calling support
    "gemma3",  # Latest with tool support
    # DeepSeek family - R1 variants support tools
    "deepseek-r1",  # Reasoning + tools (may need custom template)
    "deepseek-coder-v2",  # Coding specialized with tools
    # Specialized tool-calling models
    "firefunction",  # Optimized for function calling
    "hermes",  # Tool calling support
    "nous-hermes",  # Enhanced tool calling
]

# Models that do NOT support tool calling (common mistakes)
OLLAMA_NON_TOOL_MODELS = [
    "qwq",  # Pure reasoning model - no tool calling
    "llama4:scout",  # Large scale, capabilities unclear
    "llama4:maverick",  # Large scale, capabilities unclear
    "gemma2:2b",  # Too small for reliable tool calling
    "phi3:mini",  # Mini variants may have limited tool support
    "embedding",  # Embedding models don't do tool calling
    "bge-",  # Embedding models
    "nomic-embed",  # Embedding model
]


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider.

    Uses Ollama's OpenAI-compatible API endpoint for inference.
    Default endpoint: http://localhost:11434

    Tool calling support varies by model:
    - ✅ Qwen3, Qwen2.5, Qwen2 (all versions)
    - ✅ Llama 3.1, 3.2, 3.3, 4 (most variants)
    - ✅ Mistral, Mixtral, Mistral-Nemo
    - ✅ Command-R, Command-R-Plus
    - ✅ Phi-3, Phi-3.5, Phi-4
    - ✅ Gemma2, Gemma3
    - ✅ DeepSeek-R1, DeepSeek-Coder-v2
    - ❌ QwQ (reasoning only, no tools)
    - ❌ Embedding models (bge, nomic-embed)
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

        # First check if it's explicitly a non-tool model
        for non_tool_model in OLLAMA_NON_TOOL_MODELS:
            if non_tool_model.lower() in model_lower:
                logger.debug(
                    "ollama_model_non_tool",
                    model=self._model_name,
                    reason=f"Matches non-tool pattern: {non_tool_model}",
                )
                return False

        # Check if it matches a known tool-capable model
        is_tool_capable = any(model.lower() in model_lower for model in OLLAMA_TOOL_CAPABLE_MODELS)
        
        if is_tool_capable:
            logger.debug("ollama_model_tool_capable", model=self._model_name)
        else:
            logger.warning(
                "ollama_model_tool_unknown",
                model=self._model_name,
                message="Model not in known tool-capable list",
            )
        
        return is_tool_capable
