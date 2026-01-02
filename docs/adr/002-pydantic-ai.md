# ADR-002: Pydantic AI for Agent Orchestration

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent required an agent orchestration framework to coordinate between the local LLM (Ollama/Foundry Local), MCP tool servers, conversation management, and RAG context. The framework needed to handle complex multi-turn conversations with tool calling while maintaining type safety and simplicity.

### Requirements
- Type-safe agent framework with validation
- Native support for tool calling and function orchestration
- MCP (Model Context Protocol) integration for extensibility
- Async/await support for I/O-bound operations
- Streaming response capability
- Conversation history management
- Minimal abstraction overhead
- Compatible with local LLM providers (Ollama, Foundry Local)

### Technical Context
- Python 3.11+ runtime
- Local LLM inference via Ollama or Microsoft Foundry Local
- Multiple MCP servers (MSSQL, future extensions)
- FastAPI backend with async operations
- Type-safe data models throughout the application
- Developer familiarity with Pydantic v2 ecosystem

## Decision

We will use **Pydantic AI** as the core agent orchestration framework for the research agent.

### Implementation Details
- Use `pydantic_ai.Agent` as primary agent class
- Configure Ollama as OpenAI-compatible provider via `pydantic_ai.models.openai.OpenAIModel`
- Integrate MCP servers via `pydantic_ai.mcp.MCPServerStdio`
- Use Pydantic v2 models for all structured data (messages, results, queries)
- Leverage async context managers for MCP server lifecycle
- System prompts defined in `src/agent/prompts.py`
- Agent instantiation in `src/agent/research_agent.py`

### Key Code Pattern
```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStdio

# Configure Ollama as OpenAI-compatible
model = OpenAIModel(
    model_name="qwen3:30b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Create agent with MCP tools
agent = Agent(
    model=model,
    system_prompt="You are a SQL data analyst...",
    toolsets=[mssql_mcp_server]
)

# Use with async context manager
async with agent:
    result = await agent.run(message)
```

## Consequences

### Positive Consequences
- **Type Safety**: Full Pydantic validation for all data flows (inputs, outputs, tool calls)
- **Native MCP Support**: First-class integration with Model Context Protocol servers
- **Minimal Learning Curve**: Builds on familiar Pydantic patterns developers already know
- **Async Native**: Built for async/await from the ground up
- **LLM Agnostic**: Abstraction layer works with any OpenAI-compatible API (Ollama, Foundry, real OpenAI)
- **Structured Outputs**: Automatic parsing and validation of LLM responses
- **Tool Calling**: Native support for function calling with type-safe signatures
- **Conversation Management**: Built-in conversation history tracking
- **Streaming**: Native support for streaming token responses
- **Debugging**: Clear error messages and validation feedback
- **Ecosystem Alignment**: Integrates seamlessly with FastAPI, SQLAlchemy, Pydantic models

### Negative Consequences
- **Young Framework**: Pydantic AI is relatively new (v0.2.0) compared to alternatives
- **Limited Community**: Smaller community and fewer examples than LangChain
- **Feature Gap**: Missing some advanced features from mature frameworks (memory systems, retrieval chains)
- **API Stability**: May face breaking changes as framework matures
- **Documentation**: Less comprehensive docs compared to established frameworks
- **MCP Dependency**: Tightly couples to MCP protocol (though this aligns with project goals)

### Neutral Consequences
- **Opinionated Design**: Strong opinions about type safety and structure (matches project philosophy)
- **Python-Only**: No cross-language support (not relevant for Python-only project)
- **Manual RAG Implementation**: No built-in RAG patterns (but allows custom implementation)

## Alternatives Considered

### Alternative 1: LangChain
- **Pros:**
  - Mature framework with extensive features
  - Large community and ecosystem
  - Rich documentation and examples
  - Pre-built RAG chains and retrievers
  - Built-in memory systems
  - Wide LLM provider support
  - Vector store integrations
- **Cons:**
  - Heavy abstraction layers obscure underlying operations
  - Complex API with steep learning curve
  - Over-engineered for simple use cases
  - Frequent breaking changes between versions
  - Performance overhead from multiple abstraction layers
  - Difficult to debug when things go wrong
  - Not optimized for type safety
  - No native MCP support
- **Reason for rejection:** Violates "Simplicity First" principle; excessive abstraction for project needs

### Alternative 2: LlamaIndex
- **Pros:**
  - Excellent RAG and indexing capabilities
  - Good documentation structure
  - Strong focus on data connectors
  - Built-in query engines
  - Vector store abstractions
- **Cons:**
  - Primarily focused on RAG/indexing, less on agents
  - Complex query engine abstractions
  - Not designed around type safety
  - No MCP support
  - Less flexible for custom tool integration
  - Heavy dependency tree
- **Reason for rejection:** Optimized for RAG over agent orchestration; MCP integration not supported

### Alternative 3: Custom Agent (No Framework)
- **Pros:**
  - Complete control over implementation
  - Zero framework dependencies
  - Minimal abstraction
  - Tailored exactly to project needs
  - No learning curve for external framework
- **Cons:**
  - Must implement tool calling from scratch
  - Manual conversation history management
  - No built-in streaming support
  - Error handling complexity
  - Validation logic written manually
  - MCP integration built from ground up
  - Maintenance burden for all agent logic
- **Reason for rejection:** Significant development time for capabilities Pydantic AI provides out-of-box

### Alternative 4: Semantic Kernel (Microsoft)
- **Pros:**
  - Official Microsoft framework
  - Good integration with Azure services
  - Cross-language support (Python, C#)
  - Plugin system for tools
  - Active development by Microsoft
- **Cons:**
  - Azure-centric design
  - Less mature Python implementation (C# primary)
  - Complex plugin architecture
  - Not designed around Pydantic
  - No native MCP support
  - Heavier than needed for local-first use case
- **Reason for rejection:** Azure-centric design doesn't align with local-first philosophy

### Alternative 5: Haystack
- **Pros:**
  - Modular pipeline architecture
  - Good RAG support
  - Active community
  - Production-ready
  - Clean abstractions
- **Cons:**
  - Pipeline paradigm less suited for conversational agents
  - Not built around type safety
  - No MCP support
  - More complex than needed
  - Oriented toward production search systems
- **Reason for rejection:** Pipeline architecture doesn't fit conversational agent pattern

### Alternative 6: AutoGen (Microsoft)
- **Pros:**
  - Multi-agent orchestration
  - Interesting agent-to-agent patterns
  - Good for complex workflows
  - Microsoft-backed
- **Cons:**
  - Overkill for single-agent system
  - Complex setup for simple use cases
  - Not focused on type safety
  - No MCP support
  - Higher learning curve
- **Reason for rejection:** Multi-agent complexity not needed for single research agent

## References

- **Pydantic AI Documentation**: [ai.pydantic.dev](https://ai.pydantic.dev/)
- **Related ADRs**:
  - [ADR-006: Local-First Ollama](006-local-first-ollama.md) - LLM provider choice
- **Implementation Files**:
  - `src/agent/research_agent.py` - Agent instantiation
  - `src/agent/prompts.py` - System prompts
  - `src/mcp/client.py` - MCP server integration
  - `src/providers/ollama.py` - Ollama provider wrapper
- **Configuration**:
  - `.env`: `OLLAMA_HOST=http://localhost:11434`
  - `.env`: `OLLAMA_MODEL=qwen3:30b`
- **Dependencies**:
  - `pyproject.toml`: `pydantic-ai>=0.2.0`
  - `pyproject.toml`: `pydantic>=2.0.0`

---

**Note:** This decision should be revisited if:
1. Pydantic AI introduces breaking changes that are costly to migrate
2. MCP protocol becomes unsupported or obsolete
3. Framework maturity stalls or project becomes unmaintained
4. LangChain adds native MCP support and simplifies its API significantly
5. Project requires multi-agent orchestration patterns
