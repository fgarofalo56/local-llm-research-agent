"""
Context manager for one-shot agent queries.

Provides convenient async context manager for creating and using
research agents without manual initialization.
"""

from typing import Any

from src.providers import ProviderType

# Import at runtime to avoid circular dependency
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.core import ResearchAgent


class ResearchAgentContext:
    """
    Context manager for one-shot agent queries.

    Usage:
        async with ResearchAgentContext() as agent:
            response = await agent.chat("What tables are available?")

        # With Foundry Local:
        async with ResearchAgentContext(provider_type="foundry_local") as agent:
            response = await agent.chat("What tables are available?")
    """

    def __init__(
        self,
        provider_type: ProviderType | str | None = None,
        readonly: bool = True,
    ):
        self.provider_type = provider_type
        self.readonly = readonly
        self._agent: "ResearchAgent | None" = None

    async def __aenter__(self) -> "ResearchAgent":
        from src.agent.core import create_research_agent

        self._agent = create_research_agent(
            provider_type=self.provider_type,
            readonly=self.readonly,
        )
        return self._agent

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._agent = None
