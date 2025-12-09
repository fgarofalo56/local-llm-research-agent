"""
Base Provider Interface

Abstract base class for LLM providers (Ollama, Foundry Local, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic_ai.models.openai import OpenAIModel


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    FOUNDRY_LOCAL = "foundry_local"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider_type: ProviderType
    model_name: str
    endpoint: str
    api_key: str = ""
    timeout: int = 120
    extra_config: dict[str, Any] | None = None


@dataclass
class ProviderStatus:
    """Status information for an LLM provider."""

    available: bool
    provider_type: ProviderType
    model_name: str | None = None
    endpoint: str | None = None
    error: str | None = None
    version: str | None = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement these methods to ensure
    consistent behavior across Ollama and Foundry Local.
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the current model name."""
        pass

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """Get the API endpoint URL."""
        pass

    @abstractmethod
    def get_model(self) -> OpenAIModel:
        """
        Get a Pydantic AI compatible model instance.

        Both Ollama and Foundry Local expose OpenAI-compatible APIs,
        so we can use OpenAIModel for both.

        Returns:
            OpenAIModel configured for this provider
        """
        pass

    @abstractmethod
    async def check_connection(self) -> ProviderStatus:
        """
        Check if the provider is available and responding.

        Returns:
            ProviderStatus with connection details
        """
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """
        List available models from this provider.

        Returns:
            List of model names
        """
        pass

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """
        Check if the configured model supports tool/function calling.

        Returns:
            True if tool calling is supported
        """
        pass
