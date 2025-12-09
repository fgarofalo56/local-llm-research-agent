# Generate PRP

Generate a comprehensive Product Requirement Prompt (PRP) for implementing a new feature or module.

## Arguments: $ARGUMENTS

Read the input file or description provided in $ARGUMENTS and create a detailed PRP.

## Instructions

1. **Analyze the Request**
   - Read the input file (if provided) or interpret the description
   - Identify the core feature/functionality being requested
   - Determine which existing code patterns to follow

2. **Research Existing Codebase**
   - Use `Glob` and `Read` tools to examine relevant existing files
   - Identify patterns, conventions, and dependencies
   - Find similar implementations that can serve as examples

3. **Gather External Context**
   - Check ai_docs/ directory for relevant documentation
   - Review CLAUDE.md for project conventions
   - Note any external documentation URLs that should be referenced

4. **Create the PRP**
   Using the template at `PRPs/templates/prp_base.md`, generate a PRP with:
   
   ### Goal Section
   - Single, clear sentence describing what will be implemented
   
   ### Why Section
   - Business and technical justifications
   - How this feature fits into the larger system
   
   ### What Section
   - Concrete deliverables
   - 5-7 measurable success criteria with checkboxes
   
   ### Context Section
   - URLs to relevant documentation with explanations
   - File paths to existing code to reference
   - Specific library versions required
   - Code snippets showing patterns to follow
   
   ### Implementation Plan
   - Break into 2-4 phases
   - List specific files to create/modify per phase
   - Include implementation code examples
   - Note dependencies between phases
   
   ### Validation Checkpoints
   - How to verify each phase succeeded
   - End-to-end test criteria
   
   ### Out of Scope
   - Explicitly list what is NOT included
   - Future enhancements to defer

5. **Save the PRP**
   - Save to `PRPs/[feature-name]-prp.md`
   - Use kebab-case for filename
   - Include timestamp in commit message if committing

## Output Format

Create a markdown file in the PRPs/ directory. The PRP should be:
- Self-contained (anyone can read it and understand the full scope)
- Specific (includes actual file paths, function names, code examples)
- Testable (success criteria can be objectively verified)
- Phased (broken into logical implementation steps)

## Example Usage

```
/generate-prp INITIAL.md
/generate-prp "Add support for PostgreSQL MCP server alongside MSSQL"
/generate-prp PRPs/ideas/conversation-history.md
```

## Notes

- **IMPORTANT**: Include actual code examples from the existing codebase
- **IMPORTANT**: Reference specific files with line numbers when relevant
- Prefer linking to ai_docs/ over external URLs when documentation exists locally
- Keep the PRP focused - if scope is large, suggest splitting into multiple PRPs
