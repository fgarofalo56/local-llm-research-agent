# PRP Base Template

> **Purpose**: Use this template with `/generate-prp` command to create comprehensive Product Requirement Prompts for new features or modules.

## Goal

[Single sentence describing what will be implemented]

## Why

- [Business reason 1]
- [Business reason 2]
- [Technical reason 1]

## What

[Brief description of the deliverable]

### Success Criteria

- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]
- [ ] [Criterion that can be verified by testing]
- [ ] [Criterion that demonstrates end-to-end functionality]

## All Needed Context

### Documentation & References

- url: [URL to relevant documentation]
  why: [Why this documentation is needed]

- file: [path/to/relevant/file.py]
  why: [Why this file is needed as reference]

- doc: [path/to/ai_docs/relevant.md]
  why: [Why this documentation provides context]

### Technology Versions

```toml
# Specify versions that this PRP targets
[dependencies]
relevant_package = ">=X.Y.Z"
```

### Existing Patterns to Follow

```python
# Include code snippets showing patterns to replicate
# This helps AI understand the expected style
```

### Related Files

| File | Purpose |
|------|---------|
| `path/to/file1.py` | [What it does and why it's relevant] |
| `path/to/file2.py` | [What it does and why it's relevant] |

## Implementation Plan

### Phase 1: [Phase Name]

**Files to create/modify:**
- `path/to/new_file.py` - [Purpose]
- `path/to/existing_file.py` - [What changes]

**Key implementation details:**
```python
# Code example showing implementation approach
```

### Phase 2: [Phase Name]

**Files to create/modify:**
- [List files]

**Dependencies on Phase 1:**
- [What must be complete]

## Validation Checkpoints

1. **After Phase 1**: [How to verify success]
2. **After Phase 2**: [How to verify success]
3. **Final validation**: [End-to-end verification]

## Out of Scope

- [Feature explicitly not included]
- [Enhancement for future PRP]

## Notes for Implementation

- **IMPORTANT**: [Critical instruction]
- **IMPORTANT**: [Another critical instruction]
- [Additional guidance]
- [Edge case to handle]

---

## Template Usage Instructions

1. Copy this template to create a new PRP
2. Fill in all sections with specific details
3. Include actual code examples from the codebase
4. Link to real documentation URLs
5. Be specific about file paths and function names
6. Success criteria should be testable

### Good PRP Characteristics

✅ Specific file paths mentioned
✅ Code examples from existing codebase
✅ Clear success criteria
✅ Phased implementation plan
✅ Validation checkpoints defined
✅ Dependencies documented

### Poor PRP Characteristics

❌ Vague descriptions ("make it better")
❌ No code examples
❌ Missing file paths
❌ No success criteria
❌ Single monolithic implementation step
