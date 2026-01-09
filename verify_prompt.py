#!/usr/bin/env python3
"""
Verify agent is using the correct system prompt.
"""
import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def main():
    print("Creating agent...\n")
    
    m = MCPClientManager()
    servers = [s.name for s in m.list_servers() if s.enabled]
    
    agent = ResearchAgent(
        provider_type='ollama',
        model_name='qwen3:30b',
        readonly=True,
        mcp_servers=servers,
        cache_enabled=False
    )
    
    # Check the system prompt that was set (it's _system_prompts in Pydantic AI)
    system_prompts = agent.agent._system_prompts
    
    # Get the first system prompt
    if system_prompts:
        system_prompt = str(system_prompts[0]) if hasattr(system_prompts[0], '__str__') else system_prompts[0].content
    else:
        system_prompt = "No system prompt found"
    
    print("=" * 70)
    print("AGENT'S SYSTEM PROMPT (first 1000 chars):")
    print("=" * 70)
    print(system_prompt[:1000])
    print("\n...\n")
    
    # Check if MCP servers are mentioned
    if "MCP servers" in system_prompt or "MCP Servers" in system_prompt:
        print("✓ MCP servers ARE mentioned in system prompt")
    else:
        print("✗ MCP servers NOT mentioned in system prompt")
    
    if "mssql" in system_prompt.lower() or "MSSQL" in system_prompt:
        print("✓ MSSQL server IS mentioned")
    else:
        print("✗ MSSQL server NOT mentioned")
        
    if "analytics-management" in system_prompt.lower() or "Analytics Management" in system_prompt:
        print("✓ Analytics Management server IS mentioned")
    else:
        print("✗ Analytics Management server NOT mentioned")

asyncio.run(main())
