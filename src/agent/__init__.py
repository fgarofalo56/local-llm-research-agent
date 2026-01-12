"""Research agent for SQL Server data analytics."""

# Core agent components
from src.agent.cache import AgentCache
from src.agent.context import ResearchAgentContext
from src.agent.core import (
    OllamaConnectionError,
    ProviderConnectionError,
    ResearchAgent,
    ResearchAgentError,
    create_research_agent,
)
from src.agent.prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_MINIMAL,
    SYSTEM_PROMPT_READONLY,
    get_system_prompt,
)
from src.agent.stats import AgentStats
from src.agent.tools import (
    DocumentContent,
    KnowledgeSource,
    RAGTools,
    SearchResult,
    create_rag_tools,
)

__all__ = [
    # Agent
    "ResearchAgent",
    "ResearchAgentContext",
    "ResearchAgentError",
    "OllamaConnectionError",
    "ProviderConnectionError",
    "create_research_agent",
    # Managers
    "AgentCache",
    "AgentStats",
    # Prompts
    "SYSTEM_PROMPT",
    "SYSTEM_PROMPT_READONLY",
    "SYSTEM_PROMPT_MINIMAL",
    "get_system_prompt",
    # RAG Tools
    "RAGTools",
    "SearchResult",
    "KnowledgeSource",
    "DocumentContent",
    "create_rag_tools",
]
