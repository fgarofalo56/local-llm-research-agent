"""
LLM Provider Abstraction

Supports multiple local LLM backends:
- Ollama: Local LLM inference engine
- Foundry Local: Microsoft's local AI inference runtime
"""

from src.providers.base import LLMProvider, ProviderType
from src.providers.factory import create_provider, get_available_providers
from src.providers.foundry import FoundryLocalProvider
from src.providers.ollama import OllamaProvider

__all__ = [
    "LLMProvider",
    "ProviderType",
    "OllamaProvider",
    "FoundryLocalProvider",
    "create_provider",
    "get_available_providers",
]
