#!/usr/bin/env python3
"""
Quick test to verify agent sees MCP server tools.
"""
import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def main():
    print("Creating agent with all enabled MCP servers...")
    
    mcp_manager = MCPClientManager()
    enabled_servers = [s.name for s in mcp_manager.list_servers() if s.enabled]
    print(f"Enabled servers: {enabled_servers}\n")
    
    agent = ResearchAgent(
        provider_type="ollama",
        model_name="qwen3:30b",
        readonly=True,
        mcp_servers=enabled_servers,
    )
    
    print(f"Active toolsets: {len(agent._active_toolsets)}\n")
    
    # Test 1: Ask about tools
    print("=" * 60)
    print("TEST 1: What tools do you have?")
    print("=" * 60)
    response1 = await agent.chat("List every single tool you have access to. Be comprehensive and specific.")
    print(response1)
    print()
    
    # Test 2: Ask about analytics
    print("=" * 60)
    print("TEST 2: Can you do analytics?")
    print("=" * 60)
    response2 = await agent.chat("Can you perform data analytics operations like correlation analysis or time series analysis?")
    print(response2)
    print()
    
    # Test 3: Ask about database
    print("=" * 60)
    print("TEST 3: Can you access databases?")
    print("=" * 60)
    response3 = await agent.chat("Can you query SQL Server databases?")
    print(response3)
    print()

if __name__ == "__main__":
    asyncio.run(main())
