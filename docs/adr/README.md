# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Local LLM Research Agent project. ADRs document significant architectural decisions made during the project's evolution, including the context, rationale, consequences, and alternatives considered.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs are useful for:

- Documenting **why** certain technologies/patterns were chosen
- Providing context for new team members
- Recording trade-offs and alternatives considered
- Creating a historical record of architectural evolution
- Facilitating informed future decisions

## ADR Status

Each ADR has a status:

- **Proposed**: Under review, not yet accepted
- **Accepted**: Decision made and implemented
- **Deprecated**: No longer relevant but kept for historical context
- **Superseded**: Replaced by a newer ADR (linked bidirectionally)

## Index of ADRs

### Backend Architecture

| ADR | Title | Status | Date | Key Decision |
|-----|-------|--------|------|--------------|
| [001](001-sql-server-vectors.md) | SQL Server 2025 Native Vector Store | Accepted | 2025-01-15 | Use SQL Server 2025's native VECTOR type for RAG embeddings over specialized vector databases |
| [002](002-pydantic-ai.md) | Pydantic AI for Agent Orchestration | Accepted | 2025-01-15 | Use Pydantic AI as agent framework for type-safe MCP tool orchestration |
| [003](003-dual-database-architecture.md) | Dual Database Architecture | Accepted | 2025-01-15 | Separate SQL Server 2022 (sample data) from SQL Server 2025 (app state + vectors) |
| [006](006-local-first-ollama.md) | Ollama for Local-First LLM Inference | Accepted | 2025-01-15 | Use Ollama as primary LLM runtime for 100% local inference (privacy-first) |

### Frontend Architecture

| ADR | Title | Status | Date | Key Decision |
|-----|-------|--------|------|--------------|
| [004](004-react-frontend.md) | React 19 + Vite + TypeScript Frontend | Accepted | 2025-01-15 | Build production UI with React 19 + Vite + TypeScript (replacing Streamlit) |
| [005](005-websocket-realtime.md) | WebSocket for Real-Time Chat | Accepted | 2025-01-15 | Use WebSocket for real-time streaming of LLM tokens and agent updates |
| [007](007-zustand-state.md) | Zustand for Client State Management | Accepted | 2025-01-15 | Use Zustand for lightweight client state (UI, preferences) |

## Decision Tree

Understanding how decisions relate:

```
Privacy First Philosophy (ADR-006: Ollama)
    ↓
Local-First Architecture
    ↓
    ├─→ Backend
    │   ├─→ Type-Safe Agent (ADR-002: Pydantic AI)
    │   ├─→ Dual Databases (ADR-003: Sample vs Backend)
    │   └─→ Native Vectors (ADR-001: SQL Server 2025)
    │
    └─→ Frontend
        ├─→ Modern UI (ADR-004: React 19)
        ├─→ Real-Time (ADR-005: WebSocket)
        └─→ State Management (ADR-007: Zustand)
```

## Key Architectural Principles

The ADRs reflect these core principles:

1. **Privacy First**: All processing happens locally (ADR-006)
2. **Simplicity First**: Choose straightforward solutions over complex ones (all ADRs)
3. **Type Safety**: Leverage TypeScript and Pydantic for compile-time safety (ADR-002, 004, 007)
4. **Async by Default**: Use async/await for I/O operations (ADR-002, 005)
5. **Local-First**: No cloud dependencies for core functionality (ADR-006, 001)
6. **Separation of Concerns**: Clear boundaries between components (ADR-003)

## Technology Stack Summary

Based on these ADRs:

| Layer | Technology | ADR |
|-------|------------|-----|
| **LLM Runtime** | Ollama (qwen3:30b) | [006](006-local-first-ollama.md) |
| **Agent Framework** | Pydantic AI | [002](002-pydantic-ai.md) |
| **Sample Database** | SQL Server 2022 | [003](003-dual-database-architecture.md) |
| **Backend Database** | SQL Server 2025 | [003](003-dual-database-architecture.md) |
| **Vector Store** | SQL Server 2025 VECTOR | [001](001-sql-server-vectors.md) |
| **Backend API** | FastAPI + WebSocket | [005](005-websocket-realtime.md) |
| **Frontend Framework** | React 19 + Vite + TypeScript | [004](004-react-frontend.md) |
| **Client State** | Zustand | [007](007-zustand-state.md) |
| **Server State** | TanStack Query | [004](004-react-frontend.md) |

## Creating a New ADR

When making a significant architectural decision:

1. **Copy the template**:
   ```bash
   cp docs/adr/template.md docs/adr/XXX-title.md
   ```

2. **Follow the numbering**: Use next sequential number (e.g., 008)

3. **Fill out all sections**:
   - Context: Why is this decision needed?
   - Decision: What are we doing?
   - Consequences: What are the trade-offs?
   - Alternatives: What else did we consider?
   - References: Link related ADRs and implementation files

4. **Update this index**: Add entry to the table above

5. **Link bidirectionally**: Update related ADRs to reference new one

## Guidelines

### When to Write an ADR

Write an ADR for decisions that:
- **Affect multiple components** (not isolated implementation details)
- **Have long-term consequences** (hard to change later)
- **Involve trade-offs** (significant pros and cons)
- **Set precedents** (establish patterns for future decisions)
- **Choose between alternatives** (multiple viable options existed)

Examples of ADR-worthy decisions:
- Choosing a database or framework
- Selecting an architectural pattern
- Adopting a new technology
- Making security/compliance decisions
- Defining deployment strategies

### When NOT to Write an ADR

Don't write ADRs for:
- Implementation details (how to structure a specific function)
- Temporary workarounds or experiments
- Obvious/uncontroversial choices
- Decisions easily reversible with minimal cost
- Personal coding preferences

### ADR Best Practices

1. **Immutable**: Once accepted, ADRs should not be edited (except typos)
2. **Supersession**: Create new ADR that supersedes old one, don't modify
3. **Be Specific**: Include concrete technologies, versions, file paths
4. **Be Honest**: Document real trade-offs, not just benefits
5. **Link Implementation**: Reference actual code files that implement decision
6. **Consider Alternatives**: Show you evaluated options thoroughly
7. **Write for Future**: Assume reader has no context about current project state

## ADR Lifecycle

```
[Proposed] → [Accepted] → [Implemented]
                ↓
         [Deprecated] (if no longer applies)
                ↓
         [Superseded] (if replaced by newer ADR)
```

## References

- **ADR Process**: [Michael Nygard's ADR concept](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- **Template**: [adr/template.md](template.md)
- **Project Docs**: [../README.md](../README.md)
- **Code Context**: [../../CLAUDE.md](../../CLAUDE.md)

---

## Changelog

| Date | ADR | Change |
|------|-----|--------|
| 2025-01-15 | 001-007 | Initial ADR creation for Phase 4.3 documentation |

---

**Note**: This ADR system was created as part of Phase 4.3 to document architectural decisions made throughout the project's evolution. ADRs are dated to reflect when decisions were made, not when documented.
