# Project Overview: Local LLM Research Agent

## Purpose
A 100% local smart chat agent for SQL Server data analytics research. Uses Ollama for local LLM inference, Pydantic AI for agent orchestration, and MCP (Model Context Protocol) servers for extensible tool capabilities.

## Key Principles
- **Local-First**: All LLM inference runs locally via Ollama. No data leaves the local environment.
- **SQL Server Focus**: Works with SQL Server databases via MCP tools
- **Multi-Interface**: CLI (Typer/Rich), Web UI (Streamlit), and planned FastAPI backend

## Tech Stack
- **LLM Runtime**: Ollama (primary), Foundry Local (alternative)
- **LLM Model**: qwen3:30b (primary), qwen2.5:7b-instruct (default)
- **Agent Framework**: Pydantic AI
- **MCP Integration**: pydantic-ai[mcp] for SQL Server tools
- **Web UI**: Streamlit
- **CLI**: Typer + Rich
- **Data Validation**: Pydantic v2
- **Async Runtime**: asyncio

## Project Phases
- **Phase 1** (Complete): CLI + Streamlit + SQL Agent + Docker SQL Server
- **Phase 2.1** (In Progress): Backend Infrastructure & RAG Pipeline
- **Phase 2.2** (Planned): React UI + Full Stack

## Archon Project ID
```
16394505-e6c5-4e24-8ab4-97bd6a650cfb
```
