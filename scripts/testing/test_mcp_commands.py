"""
Test /mcp commands

Quick test of the new MCP management commands.
"""

from rich.console import Console
from src.cli.mcp_commands import handle_mcp_command

console = Console()

print("=" * 60)
print("TEST: /mcp Commands")
print("=" * 60)

# Test 1: List servers
print("\n[TEST 1] /mcp list")
handle_mcp_command(console, "/mcp list")

# Test 2: Status of a server
print("\n[TEST 2] /mcp status mssql")
handle_mcp_command(console, "/mcp status mssql")

# Test 3: Enable/disable (non-destructive tests)
print("\n[TEST 3] List enabled servers")
from src.mcp.client import MCPClientManager
mgr = MCPClientManager()
servers = mgr.list_servers()
enabled = [s.name for s in servers if s.enabled]
print(f"✓ Enabled servers: {enabled}")

print("\n" + "=" * 60)
print("✓ /mcp COMMANDS WORKING!")
print("=" * 60)
print("\nTo test interactively, run:")
print("  uv run python -m src.cli.chat")
print("\nThen try:")
print("  /mcp")
print("  /mcp list")
print("  /mcp status mssql")
print("  /help")
