# Execute PRP

Execute a Product Requirement Prompt (PRP) to implement a feature.

## Arguments: $ARGUMENTS

The path to the PRP file to execute, e.g., `PRPs/local-llm-research-agent-prp.md`

## Instructions

1. **Read and Parse the PRP**
   - Load the PRP file from $ARGUMENTS
   - Parse all sections: Goal, Why, What, Context, Implementation Plan
   - Identify the success criteria checkboxes

2. **Validate Prerequisites**
   - Check that all referenced files in the PRP exist
   - Verify required dependencies are in pyproject.toml
   - Ensure no blocking issues exist

3. **Execute Phase by Phase**

   For each phase in the Implementation Plan:
   
   a. **Announce the Phase**
      - Print what will be implemented
      - List files to be created/modified
   
   b. **Read Context**
      - Load referenced existing files
      - Review code patterns to follow
      - Check ai_docs/ for relevant documentation
   
   c. **Implement**
      - Create new files following the PRP specifications
      - Modify existing files as specified
      - Follow code examples and patterns from the PRP
      - Maintain consistency with CLAUDE.md guidelines
   
   d. **Validate**
      - Run any specified validation commands
      - Check that files were created correctly
      - Verify imports work (no circular dependencies)
   
   e. **Report Progress**
      - Mark completed items
      - Note any deviations from the plan
      - Identify any issues encountered

4. **Post-Implementation**
   - Run `uv sync` or `pip install` if dependencies changed
   - Run tests if test files were created
   - Format code with ruff
   - Lint check with ruff

5. **Final Validation**
   - Review all success criteria from the PRP
   - Check off completed criteria
   - Report any criteria that couldn't be met

## Execution Rules

- **IMPORTANT**: Execute one phase at a time, validating before proceeding
- **IMPORTANT**: If a phase fails, stop and report - don't continue blindly
- Create test files alongside implementation when specified
- Follow the exact file structure specified in the PRP
- Use existing code patterns found in the codebase
- Ask for clarification if PRP is ambiguous rather than guessing

## Output Format

After execution, provide a summary:

```markdown
## PRP Execution Summary

### ✅ Completed
- Phase 1: [Description]
- Phase 2: [Description]

### 📁 Files Created
- src/feature/new_file.py
- tests/test_feature.py

### 📝 Files Modified
- pyproject.toml (added dependency)
- src/main.py (added import)

### ✔️ Success Criteria
- [x] Criterion 1
- [x] Criterion 2
- [ ] Criterion 3 (blocked by: reason)

### ⚠️ Notes
- Any deviations from the plan
- Issues encountered and resolutions
- Recommendations for follow-up
```

## Example Usage

```
/execute-prp PRPs/local-llm-research-agent-prp.md
/execute-prp PRPs/add-postgres-support-prp.md
```

## Error Handling

If execution fails:
1. Stop at the failed step
2. Report what succeeded
3. Explain why it failed
4. Suggest how to fix
5. Do NOT proceed to the next phase

## Notes

- PRPs are designed for one-pass implementation
- If you find yourself making major deviations, stop and revise the PRP first
- Create meaningful commit messages for each phase if using git
- Prioritize correctness over speed - validate each step
