# .context Directory

This directory contains persistent context and memory for AI assistant sessions.

## Files

### SESSION_MEMORY.md
- **Purpose:** Persistent memory across Copilot CLI sessions
- **Content:** Current work state, uncommitted changes, active tasks, key decisions
- **Usage:** Read at start of each session, update before ending

### DECISIONS.md (To Be Created)
- **Purpose:** Architectural and technical decisions log
- **Content:** Why certain approaches were chosen, alternatives considered
- **Usage:** Reference when making related decisions

### TASKS.md (To Be Created)
- **Purpose:** Local task tracking (syncs with Archon when available)
- **Content:** Current tasks, priorities, blockers
- **Usage:** Task management fallback when Archon is unavailable

## Integration with Archon

When Archon MCP server is properly connected:
- Tasks sync between local TASKS.md and Archon
- Knowledge base queries enhance context
- Session memory can be enriched with project knowledge

## Workflow

**Start of Session:**
1. Read SESSION_MEMORY.md for context
2. Check git status for any new changes
3. Query Archon for active tasks (if available)
4. Continue work from where you left off

**During Session:**
- Update relevant files as context evolves
- Document important decisions in DECISIONS.md
- Track task progress

**End of Session:**
- Update SESSION_MEMORY.md with current state
- Commit work or note uncommitted changes
- Update task status in Archon/TASKS.md

## Benefits

✅ **Continuity:** Context persists across sessions
✅ **Clarity:** Always know what was being worked on
✅ **Decisions:** Track why things were done certain ways
✅ **Recovery:** Easy to resume after interruptions
✅ **Collaboration:** Team members can understand context
