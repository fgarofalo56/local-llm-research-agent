"""
Research Agent

The main AI agent that uses local LLM providers (Ollama or Foundry Local)
for inference and MCP tools for SQL Server data access.

This module re-exports components from focused submodules for backward compatibility.
All existing imports from src.agent.research_agent will continue to work.
"""

# Re-export pydantic_ai Agent for backward compatibility with tests
from pydantic_ai import Agent

# Re-export MCPClientManager for backward compatibility with tests
from src.mcp.client import MCPClientManager

# Re-export core components for backward compatibility
from src.agent.context import ResearchAgentContext
from src.agent.core import (
    OllamaConnectionError,
    ProviderConnectionError,
    ResearchAgent,
    ResearchAgentError,
    create_research_agent,
)

__all__ = [
    "Agent",
    "MCPClientManager",
    "ResearchAgent",
    "ResearchAgentContext",
    "ResearchAgentError",
    "ProviderConnectionError",
    "OllamaConnectionError",
    "create_research_agent",
]
