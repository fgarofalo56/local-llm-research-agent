# PRPs - Product Requirement Prompts

This directory contains Product Requirement Prompts (PRPs) for the Local LLM Research Analytics Tool project.

## What is a PRP?

A **Product Requirement Prompt (PRP)** is a structured prompt methodology for AI-assisted development. Unlike traditional PRDs (Product Requirement Documents) that focus on *what* to build, PRPs include the *how* - providing AI coding assistants with everything they need to implement features in a single pass.

A PRP includes:
- **Goal**: What will be implemented
- **Why**: Business and technical justification
- **What**: Success criteria and deliverables
- **Context**: Code examples, file paths, documentation references
- **Implementation Plan**: Phased approach with specific files
- **Validation**: How to verify success

## Directory Structure

```
PRPs/
├── README.md                           # This file
├── templates/
│   └── prp_base.md                     # Base template for new PRPs
├── local-llm-research-agent-prp.md     # Main project implementation PRP
└── [feature-name]-prp.md               # Future feature PRPs
```

## Using PRPs

### Generate a New PRP

Use the Claude Code command to generate a PRP from an idea or INITIAL.md file:

```
/generate-prp "Add conversation history persistence"
/generate-prp INITIAL.md
```

### Execute a PRP

Use the Claude Code command to implement a PRP:

```
/execute-prp PRPs/local-llm-research-agent-prp.md
```

### Manual PRP Creation

1. Copy `templates/prp_base.md` to a new file
2. Fill in all sections with specific details
3. Include actual code examples from the codebase
4. Define testable success criteria
5. Break implementation into phases

## Best Practices

### ✅ Good PRPs

- Include specific file paths and function names
- Reference existing code patterns to follow
- Have measurable success criteria
- Break work into 2-4 phases
- Include validation checkpoints
- Link to relevant documentation

### ❌ Poor PRPs

- Vague descriptions ("make it better")
- No code examples or patterns
- Missing file paths
- Single monolithic implementation step
- No success criteria
- Assume knowledge not in context

## Related Resources

- [Context Engineering Intro](https://github.com/coleam00/context-engineering-intro) - PRP methodology reference
- [PRPs Agentic Engineering](https://github.com/Wirasm/PRPs-agentic-eng) - Extended PRP examples
- [CLAUDE.md](../CLAUDE.md) - Project context and conventions
