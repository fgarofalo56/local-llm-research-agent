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
- **Phase 2.1** (Complete): Backend Infrastructure + RAG Pipeline + FastAPI
- **Phase 2.2** (Complete): React UI + Frontend Integration + WebSocket Chat
- **Phase 2.3** (Complete): Dashboard Builder + Advanced Visualizations
- **Phase 2.4** (Complete): Exports + Power BI MCP Integration

## Phase 2.4 Export Features
- PNG Export: High-resolution chart images (html2canvas)
- PDF Export: Multi-page reports (jspdf)
- CSV Export: Standard data export
- Excel Export: Spreadsheets with auto-column widths (xlsx)
- Dashboard JSON: Import/export configurations
- Chat Export: Markdown/PDF conversation exports
- Power BI Dialog: PBIX file creation interface

## Frontend Tech Stack (Phase 2.2+)
- **Framework**: React 19 + TypeScript + Vite
- **State Management**: TanStack Query (server), Zustand (client)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Dashboard Layout**: react-grid-layout
- **Export Libraries**: html2canvas, jspdf, xlsx, file-saver

## Archon Project ID
```
16394505-e6c5-4e24-8ab4-97bd6a650cfb
```
