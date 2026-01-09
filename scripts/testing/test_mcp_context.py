#!/usr/bin/env python3
"""
Test that agent now understands MCP servers in context.
"""
import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def main():
    print("Initializing agent with MCP server context...\n")
    
    m = MCPClientManager()
    servers = [s.name for s in m.list_servers() if s.enabled]
    
    agent = ResearchAgent(
        provider_type='ollama',
        model_name='qwen3:30b',
        readonly=True,
        mcp_servers=servers,
        cache_enabled=False  # Disable cache for fresh response
    )
    
    print(f"Enabled servers: {servers}")
    print(f"Active toolsets: {len(agent._active_toolsets)}\n")
    print("=" * 70)
    
    # Test the key question that was failing before
    question = "Do you have access to any MCP servers?"
    print(f"\nQ: {question}")
    print("-" * 70)
    
    response = await agent.chat(question)
    print(response)
    print("\n" + "=" * 70)
    
    # Also test alternate phrasing
    question2 = "What tools do you have?"
    print(f"\nQ: {question2}")
    print("-" * 70)
    
    response2 = await agent.chat(question2)
    print(response2)
    print("\n" + "=" * 70)

asyncio.run(main())
