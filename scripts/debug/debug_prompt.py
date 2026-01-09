#!/usr/bin/env python3
"""
Debug system prompt generation.
"""
from src.agent.prompts import format_mcp_servers_info, get_system_prompt

# Test MCP info generation
enabled_servers = ['mssql', 'analytics-management', 'data-analytics']
mcp_info = format_mcp_servers_info(enabled_servers)

print("=" * 70)
print("MCP SERVERS INFO:")
print("=" * 70)
print(mcp_info)
print()

# Test system prompt generation
prompt = get_system_prompt(
    readonly=True,
    mcp_servers_info=mcp_info
)

print("=" * 70)
print("SYSTEM PROMPT (first 1500 chars):")
print("=" * 70)
print(prompt[:1500])
print("\n...\n")
print(prompt[-500:])
