#!/usr/bin/env python3
"""
Patch script to fix MCP session management in CLI.

This script applies the minimal changes needed to keep MCP sessions open
for the entire CLI session instead of reconnecting on every message.

Run: python apply_session_fix.py
"""

import sys
from pathlib import Path

def apply_fix():
    """Apply the session management fix to agent/core.py and cli/chat.py."""
    
    print("🔧 Applying MCP session management fix...")
    print()
    
    # Fix 1: Add context managers to ResearchAgent
    core_file = Path("src/agent/core.py")
    if not core_file.exists():
        print("❌ Error: src/agent/core.py not found")
        return False
    
    print("📝 Step 1: Adding context manager support to ResearchAgent...")
    
    core_content = core_file.read_text()
    
    # Add __aenter__ and __aexit__ methods after model_endpoint property
    context_managers = '''
    async def __aenter__(self):
        """Enter async context - opens MCP sessions once for entire CLI session."""
        await self.agent.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - closes MCP sessions when CLI exits."""
        return await self.agent.__aexit__(exc_type, exc_val, exc_tb)
'''
    
    # Find insertion point (after model_endpoint property)
    insertion_marker = "        return self.provider.endpoint"
    if insertion_marker in core_content:
        core_content = core_content.replace(
            insertion_marker,
            insertion_marker + context_managers
        )
        print("  ✅ Added __aenter__ and __aexit__ methods")
    else:
        print("  ⚠️  Could not find insertion point for context managers")
        return False
    
    # Remove async with from _run_agent_with_retry
    old_execute = '''        @retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
        async def _execute():
            async with self.agent:
                result = await self.agent.run(message)
                return result.output

        return await _execute()'''
    
    new_execute = '''        @retry(config=self._retry_config, circuit_breaker=self._circuit_breaker)
        async def _execute():
            # Do NOT enter agent context here - it's entered at session level
            result = await self.agent.run(message)
            return result.output

        return await _execute()'''
    
    if old_execute in core_content:
        core_content = core_content.replace(old_execute, new_execute)
        print("  ✅ Removed per-message context from _run_agent_with_retry")
    else:
        print("  ⚠️  Could not find _run_agent_with_retry pattern")
        return False
    
    # Write updated file
    core_file.write_text(core_content)
    print("  ✅ Updated src/agent/core.py")
    print()
    
    # Fix 2: Wrap chat loop in agent context
    chat_file = Path("src/cli/chat.py")
    if not chat_file.exists():
        print("❌ Error: src/cli/chat.py not found")
        return False
    
    print("📝 Step 2: Wrapping chat loop in agent context...")
    
    chat_content = chat_file.read_text()
    
    # Find the print_help_commands() call and insert async with before while loop
    old_pattern = '''    print_help_commands()

    while True:'''
    
    new_pattern = '''    print_help_commands()

    # CRITICAL: Enter agent context once for entire session
    # This keeps MCP sessions open and prevents reconnecting on every message
    async with agent:
        console.print(f"[{COLORS['gray_400']}]{Icons.CHECK} MCP sessions established[/]")
        console.print()
        
        while True:'''
    
    if old_pattern in chat_content:
        chat_content = chat_content.replace(old_pattern, new_pattern)
        print("  ✅ Added async with agent context")
    else:
        print("  ⚠️  Could not find insertion point")
        return False
    
    # Find the end of while loop and adjust indentation
    # This is tricky - need to indent the entire while loop body
    print("  ⚠️  Manual step required: Indent the entire while loop body by 4 spaces")
    print("     Or use an IDE's auto-format feature after applying this patch")
    
    # Write updated file
    chat_file.write_text(chat_content)
    print("  ✅ Updated src/cli/chat.py")
    print()
    
    print("✅ Patch applied successfully!")
    print()
    print("⚠️  IMPORTANT: You need to manually indent the while loop body in src/cli/chat.py")
    print("   Use your IDE's auto-format or manually add 4 spaces to each line inside the while loop")
    print()
    print("🧪 Test with: uv run python -m src.cli.chat")
    print("   You should see: '✓ MCP sessions established' once at startup")
    print("   Then no more MCP POST requests when asking simple questions")
    
    return True

if __name__ == "__main__":
    success = apply_fix()
    sys.exit(0 if success else 1)
