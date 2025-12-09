# 📚 Documentation

> **Complete documentation for the Local LLM Research Agent**

---

## 📑 Table of Contents

- [Quick Links](#-quick-links)
- [Documentation Structure](#-documentation-structure)
- [Getting Started](#-getting-started)
- [Guides](#-guides)
- [Reference](#-reference)
- [Architecture](#-architecture)

---

## 🔗 Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](guides/getting-started.md) | Quick start guide for new users |
| [Configuration](guides/configuration.md) | Environment variables and settings |
| [Troubleshooting](guides/troubleshooting.md) | Common issues and solutions |
| [MCP Tools Reference](reference/mssql_mcp_tools.md) | SQL Server MCP tool documentation |
| [Pydantic AI Integration](reference/pydantic_ai_mcp.md) | Agent framework reference |

---

## 📁 Documentation Structure

```
docs/
├── README.md                 # This file - documentation index
├── guides/
│   ├── getting-started.md    # Quick start guide
│   ├── configuration.md      # Configuration reference
│   ├── troubleshooting.md    # Problem-solving guide
│   └── DOCUMENTATION-STANDARDS.md  # Doc style guide
├── reference/
│   ├── mssql_mcp_tools.md    # MSSQL MCP Server tools
│   └── pydantic_ai_mcp.md    # Pydantic AI MCP integration
├── diagrams/
│   └── architecture.excalidraw  # System architecture diagram
└── api/
    └── (future API docs)
```

---

## 🚀 Getting Started

New to the project? Start here:

1. **[Getting Started Guide](guides/getting-started.md)** - Complete setup walkthrough
2. **[Docker Setup](../docker/README.md)** - SQL Server with sample data
3. **[Configuration](guides/configuration.md)** - Environment setup

---

## 📖 Guides

| Guide | Purpose |
|-------|---------|
| [Getting Started](guides/getting-started.md) | First-time setup and basic usage |
| [Configuration](guides/configuration.md) | All environment variables explained |
| [Troubleshooting](guides/troubleshooting.md) | Fix common issues |
| [Documentation Standards](guides/DOCUMENTATION-STANDARDS.md) | How to write docs for this project |

---

## 📋 Reference

| Reference | Purpose |
|-----------|---------|
| [MSSQL MCP Tools](reference/mssql_mcp_tools.md) | SQL Server MCP tool documentation |
| [Pydantic AI MCP](reference/pydantic_ai_mcp.md) | Agent framework integration |

---

## 🏗️ Architecture

The system architecture is documented in the [architecture diagram](diagrams/architecture.excalidraw).

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    🖥️ User Interfaces                       │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │  ⌨️ CLI (Typer)  │              │  🌐 Streamlit UI    │   │
│  └────────┬────────┘              └──────────┬──────────┘   │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   🤖 Pydantic AI Agent                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  System Prompt + Tool Orchestration + Conversation    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────┐       ┌─────────────────────────────────┐
│   🦙 Ollama       │       │        🔌 MCP Servers           │
│   (Local LLM)     │       │  ┌───────────────────────────┐  │
│                   │       │  │  🗄️ MSSQL MCP Server      │  │
│ qwen2.5/llama3.1  │       │  └─────────────┬─────────────┘  │
└───────────────────┘       │                │                │
                            │                ▼                │
                            │  ┌───────────────────────────┐  │
                            │  │  🗃️ SQL Server 2022       │  │
                            │  │    (Docker Container)     │  │
                            │  └───────────────────────────┘  │
                            └─────────────────────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| 🦙 LLM Runtime | Ollama | Local model inference |
| 🤖 Agent Framework | Pydantic AI | Orchestration & tools |
| 🔌 MCP Server | MSSQL MCP (Node.js) | SQL Server access |
| 🌐 Web UI | Streamlit | Browser interface |
| ⌨️ CLI | Typer + Rich | Terminal interface |
| 🗃️ Database | SQL Server 2022 | Data storage |

---

## 🔐 Security

- **100% Local** - All processing on your machine
- **No Cloud APIs** - Data never leaves your network
- **Read-only Mode** - Safe exploration option
- See [SECURITY.md](../SECURITY.md) for full security policy

---

## 🤝 Contributing

Documentation contributions are welcome! Please follow the [Documentation Standards](guides/DOCUMENTATION-STANDARDS.md).

---

*Last Updated: December 2024*
