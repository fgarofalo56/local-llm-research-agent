# 📋 Documentation Standards

> **Visual documentation guidelines for the Local LLM Research Agent project**

---

## 🎨 Visual Standards

This project uses consistent visual elements to make documentation clear, scannable, and professional.

### Emoji Icons by Section Type

| Section Type | Icon | Usage |
|--------------|------|-------|
| Overview/Introduction | 🎯 | Main purpose statements |
| Installation/Setup | 📦 | Package/dependency sections |
| Configuration | ⚙️ | Settings and environment variables |
| Deployment | 🚀 | Deployment instructions |
| Security | 🔐 | Security-related content |
| Database | 🗄️ | Database schemas and queries |
| API/Integration | 🔌 | API endpoints and integrations |
| Monitoring | 📊 | Logging, metrics, observability |
| Troubleshooting | 🔧 | Problem-solving guides |
| Best Practices | 🏆 | Recommendations |
| Warning/Caution | ⚠️ | Important gotchas |
| Tips | 💡 | Helpful suggestions |
| Code | 💻 | Code examples |
| Files/Folders | 📁 | File structure |
| Resources/Links | 📚 | External references |
| Table of Contents | 📑 | Navigation |

### Project Component Icons

| Component | Icon | Description |
|-----------|------|-------------|
| Ollama / LLM | 🦙 | Local LLM inference |
| Pydantic AI Agent | 🤖 | Agent orchestration |
| MCP Server | 🔌 | Model Context Protocol |
| SQL Server | 🗃️ | Database storage |
| Docker | 🐳 | Container runtime |
| CLI Interface | ⌨️ | Command line |
| Web UI | 🌐 | Streamlit interface |
| Configuration | ⚙️ | Settings |

---

## 📝 Markdown Formatting

### Headers

```markdown
# 🎯 Main Title (H1 - only one per document)

## 📑 Major Section (H2)

### Subsection (H3)

#### Detail Section (H4)
```

### Tables

Always use tables for:
- Configuration options
- Comparisons
- Feature lists
- Status indicators

```markdown
| Feature | Status | Notes |
|---------|--------|-------|
| Tool calling | ✅ | Qwen2.5 recommended |
| Local inference | ✅ | 100% on-device |
| Cloud APIs | ❌ | Not used |
```

### Status Indicators

| Indicator | Meaning |
|-----------|---------|
| ✅ | Complete/Supported/Yes |
| ❌ | Not supported/No |
| ⚠️ | Warning/Caution |
| 🔄 | In progress |
| 📌 | Important/Pinned |
| 🆕 | New feature |
| 🔜 | Coming soon |

### Code Blocks

Always specify language for syntax highlighting:

````markdown
```python
def process_query(message: str) -> dict:
    """Process a natural language query."""
    pass
```

```bash
# Start the agent
uv run python -m src.cli.chat
```

```json
{
  "setting": "value"
}
```
````

### Callouts (Blockquotes)

Use for important information:

```markdown
> **Note:** Important information here

> ⚠️ **Warning:** Critical gotcha or caution

> 💡 **Tip:** Helpful suggestion
```

---

## 📁 Documentation Structure

### Required Files

```
docs/
├── README.md                    # Documentation index
├── guides/
│   ├── getting-started.md       # Quick start guide
│   ├── configuration.md         # Configuration reference
│   ├── troubleshooting.md       # Troubleshooting guide
│   └── DOCUMENTATION-STANDARDS.md # This file
├── reference/
│   ├── mssql_mcp_tools.md       # MCP tools reference
│   └── pydantic_ai_mcp.md       # Pydantic AI integration
├── diagrams/
│   └── architecture.excalidraw  # Main architecture
└── api/
    └── (future API docs)
```

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| Guides | `kebab-case.md` | `getting-started.md` |
| Reference | `technology_name.md` | `mssql_mcp_tools.md` |
| Diagrams | `diagram-name.excalidraw` | `architecture.excalidraw` |
| Standards | `SCREAMING-KEBAB.md` | `DOCUMENTATION-STANDARDS.md` |

---

## 📊 Diagram Standards

### Excalidraw Conventions

**Color Scheme:**

| Element | Color | Hex Code |
|---------|-------|----------|
| User Interface | Blue | `#deebff` / `#0078D4` |
| Agent/AI | Orange | `#fef3c7` / `#F59E0B` |
| LLM/Ollama | Purple | `#ede9fe` / `#7C3AED` |
| MCP/Integration | Green | `#d1fae5` / `#059669` |
| Database | Gray | `#f3f4f6` / `#6B7280` |
| Docker | Cyan | `#e0f2fe` / `#0EA5E9` |

**Arrow Conventions:**

| Style | Meaning |
|-------|---------|
| Solid line | Data flow |
| Dashed line | Configuration/secrets |
| Thick line | Primary flow |
| Thin line | Secondary flow |

**Export Requirements:**

1. Export as `.excalidraw` (source)
2. Export as `.png` with embedded scene data
3. Use 2x resolution for clarity
4. Include in git commits

---

## ✍️ Writing Style

### Tone

- **Professional** but approachable
- **Concise** - avoid unnecessary words
- **Action-oriented** - use imperative mood for instructions
- **Consistent** - use same terms throughout

### Voice

| ✅ Do | ❌ Don't |
|-------|---------|
| "Run the following command" | "You should run this command" |
| "Configure the settings" | "The settings should be configured" |
| "The agent processes queries" | "Queries are processed by the agent" |

### Technical Terms

- Use consistent terminology
- Define acronyms on first use
- Link to glossary for complex terms

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol |
| **LLM** | Large Language Model |
| **MSSQL** | Microsoft SQL Server |
| **CLI** | Command Line Interface |

---

## 🔄 Maintenance

### Update Checklist

When updating documentation:

- [ ] Update relevant diagrams
- [ ] Check all code examples still work
- [ ] Update version numbers
- [ ] Verify links are not broken
- [ ] Update "Last Updated" date
- [ ] Review for consistency with standards

### Version Footer

Every document should end with:

```markdown
---

*Last Updated: [Month Year]*
```

---

## 📚 Templates

### New Guide Template

```markdown
# 🎯 [Guide Title]

> **[One-line description of what this guide covers]**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Prerequisites](#-prerequisites)
- [Steps](#-steps)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

[Brief description of the topic]

## 📦 Prerequisites

- [ ] Prerequisite 1
- [ ] Prerequisite 2

## 🚀 Steps

### Step 1: [Action]

[Instructions]

### Step 2: [Action]

[Instructions]

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| [Problem] | [Fix] |

---

*Last Updated: [Month Year]*
```

### New Reference Doc Template

```markdown
# [Icon] [Reference Title]

> **[One-line purpose statement]**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Best Practices](#-best-practices)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

[Why this component is used in the project]

## ⚙️ Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| [Setting] | [Value] | [Notes] |

## 💻 Usage

```python
# Code example
```

## 🏆 Best Practices

- Best practice 1
- Best practice 2

## 🔧 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| [Issue] | [Cause] | [Solution] |

---

*Last Updated: [Month Year]*
```

---

*Last Updated: December 2024*
