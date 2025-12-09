"""
Provider Factory

Factory functions for creating LLM provider instances.
"""

from src.providers.base import LLMProvider, ProviderStatus, ProviderType
from src.providers.foundry import FoundryLocalProvider
from src.providers.ollama import OllamaProvider
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_provider(
    provider_type: ProviderType | str | None = None,
    model_name: str | None = None,
    endpoint: str | None = None,
    **kwargs,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider_type: Provider type (ollama, foundry_local) or None for auto-detect
        model_name: Model name/alias (uses settings default if not provided)
        endpoint: API endpoint URL (uses settings default if not provided)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider_type is invalid
    """
    # Convert string to enum if needed
    if isinstance(provider_type, str):
        try:
            provider_type = ProviderType(provider_type.lower())
        except ValueError:
            raise ValueError(
                f"Invalid provider type: {provider_type}. "
                f"Valid options: {[p.value for p in ProviderType]}"
            )

    # Auto-detect from settings if not specified
    if provider_type is None:
        provider_type = ProviderType(settings.llm_provider)

    if provider_type == ProviderType.OLLAMA:
        return OllamaProvider(
            model_name=model_name or settings.ollama_model,
            host=endpoint or settings.ollama_host,
            **kwargs,
        )
    elif provider_type == ProviderType.FOUNDRY_LOCAL:
        return FoundryLocalProvider(
            model_name=model_name or settings.foundry_model,
            endpoint=endpoint or settings.foundry_endpoint,
            **kwargs,
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")


async def get_available_providers() -> list[ProviderStatus]:
    """
    Check which providers are currently available.

    Returns:
        List of ProviderStatus for each configured provider
    """
    statuses = []

    # Check Ollama
    try:
        ollama = OllamaProvider(
            model_name=settings.ollama_model,
            host=settings.ollama_host,
        )
        status = await ollama.check_connection()
        statuses.append(status)
    except Exception as e:
        statuses.append(
            ProviderStatus(
                available=False,
                provider_type=ProviderType.OLLAMA,
                error=str(e),
            )
        )

    # Check Foundry Local
    try:
        foundry = FoundryLocalProvider(
            model_name=settings.foundry_model,
            endpoint=settings.foundry_endpoint,
        )
        status = await foundry.check_connection()
        statuses.append(status)
    except Exception as e:
        statuses.append(
            ProviderStatus(
                available=False,
                provider_type=ProviderType.FOUNDRY_LOCAL,
                error=str(e),
            )
        )

    return statuses


async def auto_select_provider() -> LLMProvider | None:
    """
    Automatically select the first available provider.

    Checks providers in order of preference:
    1. Configured provider from settings
    2. Ollama
    3. Foundry Local

    Returns:
        Available LLMProvider or None if none available
    """
    # First try the configured provider
    try:
        provider = create_provider()
        status = await provider.check_connection()
        if status.available:
            logger.info(
                "auto_select_provider",
                provider=provider.provider_type.value,
                model=provider.model_name,
            )
            return provider
    except Exception:
        pass

    # Try each provider in order
    for ptype in ProviderType:
        try:
            provider = create_provider(provider_type=ptype)
            status = await provider.check_connection()
            if status.available:
                logger.info(
                    "auto_select_provider_fallback",
                    provider=ptype.value,
                    model=provider.model_name,
                )
                return provider
        except Exception:
            continue

    logger.warning("no_providers_available")
    return None
