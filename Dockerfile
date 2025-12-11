# =============================================================================
# Dockerfile for Local LLM Research Agent
#
# Multi-stage build for optimized image size.
# Includes Python application and MSSQL MCP Server (Node.js).
#
# Usage:
#   docker build -t local-llm-agent .
#   docker run -it --rm --env-file .env local-llm-agent chat
#   docker run -it --rm --env-file .env -p 8501:8501 local-llm-agent ui
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build MSSQL MCP Server (Node.js)
# -----------------------------------------------------------------------------
FROM node:20-slim AS mcp-builder

WORKDIR /mcp

# Clone and build MSSQL MCP Server
RUN apt-get update && apt-get install -y git ca-certificates \
    && git clone --depth 1 https://github.com/Azure-Samples/SQL-AI-samples.git \
    && cd SQL-AI-samples/MssqlMcp/Node \
    && npm install \
    && npm run build \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 2: Python Application
# -----------------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="Local LLM Research Agent"
LABEL description="100% local smart chat agent for SQL Server data analytics"
LABEL version="0.1.0"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Application paths
    APP_HOME=/app \
    MCP_MSSQL_PATH=/opt/mssql-mcp/dist/index.js \
    # Default LLM provider (expects external Ollama service)
    LLM_PROVIDER=ollama \
    OLLAMA_HOST=http://host.docker.internal:11434 \
    # Streamlit configuration
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR ${APP_HOME}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Node.js runtime for MCP server
    nodejs \
    # Required for health checks
    curl \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy MCP server from builder stage
COPY --from=mcp-builder /mcp/SQL-AI-samples/MssqlMcp/Node /opt/mssql-mcp

# Install Python dependencies
COPY pyproject.toml requirements*.txt* ./
RUN pip install --no-cache-dir -e . \
    || pip install --no-cache-dir pydantic-ai pydantic streamlit typer rich python-dotenv pydantic-settings structlog httpx

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/

# Create non-root user for security
RUN groupadd --gid 1000 agent \
    && useradd --uid 1000 --gid agent --shell /bin/bash --create-home agent \
    && chown -R agent:agent ${APP_HOME} \
    && mkdir -p /home/agent/.local-llm-agent \
    && chown -R agent:agent /home/agent/.local-llm-agent

USER agent

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - supports both CLI and UI modes
# Use exec form for proper signal handling
# Override with docker-compose command for different modes
CMD ["python", "-m", "src.cli.chat"]
