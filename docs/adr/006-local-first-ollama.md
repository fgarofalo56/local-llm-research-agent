# ADR-006: Ollama for Local-First LLM Inference

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent required a Large Language Model (LLM) provider for natural language understanding, SQL query generation, and conversational responses. The choice of LLM provider would fundamentally shape the project's architecture, privacy model, and user experience.

### Core Requirements
- **100% local execution** - No data sent to external APIs
- **Privacy-first** - Sensitive research data never leaves local network
- **Tool calling support** - Ability to call MCP server tools
- **Streaming responses** - Token-by-token generation for better UX
- **Model flexibility** - Ability to swap/test different models
- **OpenAI API compatibility** - Standard interface for agent frameworks
- **Production-ready** - Stable, well-maintained solution
- **Developer-friendly** - Easy setup and debugging

### Technical Context
- Target hardware: High-performance workstation (RTX 5090 32GB, 128GB RAM)
- Windows 11 Enterprise environment
- Pydantic AI agent framework (requires OpenAI-compatible provider)
- MCP tool integration requiring function calling
- Document embeddings for RAG pipeline (768 dimensions)
- Development team familiar with local tools, not cloud services

### Privacy & Security Considerations
- Research data may contain sensitive institutional information
- Compliance with data residency requirements
- No external API keys or cloud accounts
- Full control over data flow and logging
- Air-gapped deployment capability

## Decision

We will use **Ollama** as the primary LLM inference runtime for local model execution, with **Microsoft Foundry Local** as an alternative provider.

### Implementation Details

**Primary Provider: Ollama**
- Runtime: Ollama server (http://localhost:11434)
- Primary model: `qwen3:30b` (Mixture-of-Experts, 18GB VRAM)
- Embedding model: `nomic-embed-text` (768 dimensions)
- API: OpenAI-compatible endpoint (`/v1/chat/completions`)
- Integration: via `pydantic_ai.models.openai.OpenAIModel`

**Alternative Provider: Microsoft Foundry Local**
- Runtime: Foundry Local service (http://127.0.0.1:53760)
- Models: `phi-4`, `phi-3-mini`
- API: OpenAI-compatible
- Use case: Smaller models, faster inference for simple queries

**Configuration**:
```python
# Ollama
model = OpenAIModel(
    model_name="qwen3:30b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Dummy key, not validated
)

# Foundry Local
model = OpenAIModel(
    model_name="phi-4",
    base_url="http://127.0.0.1:53760/v1",
    api_key="not-needed"
)
```

### Model Selection Rationale
| Model | Size | Use Case | Tool Calling | Speed |
|-------|------|----------|--------------|-------|
| **qwen3:30b** | 18GB | Primary (best tool calling) | Excellent | Fast (MoE) |
| qwen3:32b | 20GB | Alternative (better quality) | Excellent | Medium |
| qwq:latest | 19GB | Complex reasoning | Good | Medium |
| phi-4 | 7GB | Fast queries (Foundry) | Good | Very fast |

## Consequences

### Positive Consequences
- **100% Privacy**: All inference happens locally; data never transmitted externally
- **Zero API Costs**: No usage fees, no rate limits, no quotas
- **Data Sovereignty**: Complete control over data residency and compliance
- **Offline Capable**: Works without internet connection (air-gapped deployments)
- **Model Flexibility**: Easy to pull/test different models (`ollama pull model-name`)
- **OpenAI Compatible**: Standard API works with Pydantic AI and other frameworks
- **Hardware Utilization**: Fully leverages RTX 5090's 32GB VRAM
- **No Vendor Lock-in**: Can switch models or providers without code changes
- **Developer Experience**: Local setup (`ollama pull`, `ollama run`) simpler than cloud credentials
- **Debugging**: Full access to logs, metrics, model behavior
- **Latency**: Local inference faster than API round-trips (no network overhead)
- **Customization**: Can fine-tune models or run custom quantizations
- **Community**: Large Ollama community with model library

### Negative Consequences
- **Hardware Requirement**: Requires powerful GPU (RTX 5090 or similar)
- **Model Download**: Initial model pull requires bandwidth (18GB for qwen3:30b)
- **Setup Complexity**: Users must install Ollama separately (not a Python package)
- **VRAM Constraints**: Limited to models that fit in 32GB (can't run 70B+ models fully)
- **Model Quality**: Local models may underperform GPT-4/Claude-Opus for complex reasoning
- **Tool Calling Maturity**: Smaller models have less reliable function calling than GPT-4
- **Maintenance**: Must manually update Ollama and pull new model versions
- **Multi-User Scaling**: Single GPU shared across users (queuing)
- **No Fine-Tuning UI**: Limited fine-tuning ecosystem compared to cloud providers

### Neutral Consequences
- **Model Ecosystem**: Growing but smaller than OpenAI/Anthropic model catalogs
- **Windows Support**: Ollama supports Windows (no cross-platform issues)
- **CPU Fallback**: Can run on CPU if GPU unavailable (very slow)

## Alternatives Considered

### Alternative 1: OpenAI API (GPT-4)
- **Pros:**
  - Best-in-class model quality
  - Excellent tool calling reliability
  - No local hardware requirements
  - Latest features (GPT-4 Turbo, vision, etc.)
  - Stable API with good uptime
  - Comprehensive documentation
- **Cons:**
  - **Privacy violation**: All data sent to OpenAI servers
  - API costs per token (expensive at scale)
  - Requires API key and OpenAI account
  - Internet dependency
  - Data residency concerns
  - Rate limits
  - No offline capability
  - Vendor lock-in
- **Reason for rejection:** Fundamentally violates "100% local" and privacy-first principles

### Alternative 2: Anthropic Claude API
- **Pros:**
  - Excellent reasoning and safety
  - Good tool calling (Claude 3.5+)
  - Longer context windows
  - Strong following instructions
- **Cons:**
  - **Privacy violation**: Cloud API
  - Expensive API costs
  - No local deployment option
  - Internet required
  - Data leaves premises
- **Reason for rejection:** Same privacy concerns as OpenAI

### Alternative 3: Azure OpenAI Service
- **Pros:**
  - Enterprise features (security, compliance)
  - Data residency controls
  - SLA guarantees
  - Integration with Azure services
- **Cons:**
  - **Not local**: Cloud service (even if private endpoint)
  - Azure account required
  - API costs
  - Complex setup (networking, auth)
  - Overkill for single-user deployment
- **Reason for rejection:** Cloud-based, not aligned with local-first philosophy

### Alternative 4: Hugging Face Transformers (Direct)
- **Pros:**
  - Python library (no separate runtime)
  - Direct model access
  - Full control over inference
  - Free and open source
  - Extensive model library
- **Cons:**
  - Complex setup (PyTorch, CUDA, model loading)
  - Manual quantization and optimization
  - No built-in API server
  - Must handle batching/queueing manually
  - Significant development overhead
  - No standard API (custom integration per model)
  - Tool calling must be implemented from scratch
- **Reason for rejection:** Too much low-level complexity; Ollama provides better abstraction

### Alternative 5: LocalAI
- **Pros:**
  - OpenAI-compatible API
  - Supports multiple backends (llama.cpp, ggml)
  - Docker deployment
  - Good for heterogeneous setups
- **Cons:**
  - Less polished than Ollama
  - Smaller community
  - More complex configuration
  - Performance not as optimized
  - Less frequent updates
  - Tool calling support varies by backend
- **Reason for rejection:** Ollama more mature and better maintained

### Alternative 6: llama.cpp (Direct)
- **Pros:**
  - C++ performance
  - Low-level control
  - Efficient inference
  - Supports all GGUF models
- **Cons:**
  - No HTTP API out-of-box (need separate server)
  - C++ build complexity
  - Manual model conversion
  - No OpenAI API compatibility
  - Python bindings less ergonomic
  - Must implement tool calling logic
- **Reason for rejection:** Too low-level; Ollama built on llama.cpp with better UX

### Alternative 7: vLLM
- **Pros:**
  - High-throughput inference
  - Advanced batching
  - Production-grade
  - OpenAI API compatible
- **Cons:**
  - Complex setup
  - Designed for multi-user server deployment
  - Overkill for single-user
  - Limited Windows support
  - More resource-intensive
- **Reason for rejection:** Over-engineered for single-user local deployment

### Alternative 8: LM Studio
- **Pros:**
  - User-friendly GUI
  - Easy model management
  - Good for non-technical users
  - OpenAI API compatible
- **Cons:**
  - Desktop app (not automation-friendly)
  - Less scriptable than Ollama CLI
  - Smaller model library
  - Windows/Mac focus (limited Linux)
  - Not as developer-focused
- **Reason for rejection:** Ollama's CLI better for development workflow

## References

- **Ollama Documentation**: [ollama.com/docs](https://ollama.com/)
- **Ollama GitHub**: [github.com/ollama/ollama](https://github.com/ollama/ollama)
- **Ollama Model Library**: [ollama.com/library](https://ollama.com/library)
- **Microsoft Foundry Local**: [github.com/microsoft/Foundry-Local](https://github.com/microsoft/Foundry-Local)
- **Related ADRs**:
  - [ADR-002: Pydantic AI](002-pydantic-ai.md) - Agent framework requiring OpenAI-compatible API
  - [ADR-005: WebSocket Real-time](005-websocket-realtime.md) - Streaming tokens from Ollama
- **Implementation Files**:
  - `src/providers/ollama.py` - Ollama provider wrapper
  - `src/providers/foundry.py` - Foundry Local provider
  - `src/providers/factory.py` - Provider factory (selects based on env)
  - `src/rag/embedder.py` - Ollama embeddings for RAG
- **Configuration**:
  - `.env`: `OLLAMA_HOST=http://localhost:11434`
  - `.env`: `OLLAMA_MODEL=qwen3:30b`
  - `.env`: `EMBEDDING_MODEL=nomic-embed-text`
  - `.env`: `FOUNDRY_ENDPOINT=http://127.0.0.1:53760`
  - `CLAUDE.md`: Model recommendations for RTX 5090

---

**Note:** This decision should be revisited if:
1. Cloud deployment becomes required (consider Azure OpenAI with private endpoint)
2. Model quality requirements exceed local model capabilities
3. Hardware constraints change (smaller GPU, need CPU inference)
4. Ollama project becomes unmaintained or deprecated
5. Privacy requirements relax (allows cloud APIs)
6. Multi-user scale requires dedicated inference servers (consider vLLM)
