"""Research agent for SQL Server data analytics."""

from src.agent.prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_MINIMAL,
    SYSTEM_PROMPT_READONLY,
    get_system_prompt,
)
from src.agent.research_agent import (
    OllamaConnectionError,
    ResearchAgent,
    ResearchAgentContext,
    ResearchAgentError,
    create_research_agent,
)

__all__ = [
    # Agent
    "ResearchAgent",
    "ResearchAgentContext",
    "ResearchAgentError",
    "OllamaConnectionError",
    "create_research_agent",
    # Prompts
    "SYSTEM_PROMPT",
    "SYSTEM_PROMPT_READONLY",
    "SYSTEM_PROMPT_MINIMAL",
    "get_system_prompt",
]
