"""
Quick Test: Chat Methods
=========================

Minimal test script without fancy UI - just the essentials.
Good for quick verification or debugging.
"""

import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

async def main():
    print("\n" + "="*60)
    print("Quick Chat Methods Test")
    print("="*60)
    
    # Setup
    print("\n1. Creating agent...")
    mcp_manager = MCPClientManager()
    agent = ResearchAgent(mcp_servers=["mssql", "archon"])
    
    print("2. Entering agent context...")
    async with agent:
        print("   ✓ MCP sessions established\n")
        
        # Test 1: Basic chat
        print("="*60)
        print("TEST 1: chat() - Basic response")
        print("="*60)
        response = await agent.chat("What tables exist?")
        print(f"Response: {response[:150]}...")
        print(f"Length: {len(response)} chars\n")
        
        # Test 2: Streaming
        print("="*60)
        print("TEST 2: chat_stream() - Streaming")
        print("="*60)
        print("Response: ", end="", flush=True)
        async for chunk in agent.chat_stream("List 3 researchers"):
            print(chunk, end="", flush=True)
        print()
        stats = agent.get_last_response_stats()
        print(f"Stats: {stats.get('token_usage', 'N/A')}\n")
        
        # Test 3: Detailed
        print("="*60)
        print("TEST 3: chat_with_details() - Full metadata")
        print("="*60)
        response = await agent.chat_with_details("Count active projects")
        print(f"Content: {response.content[:150]}...")
        print(f"Model: {response.model}")
        print(f"Duration: {response.duration_ms:.0f}ms")
        print(f"Tokens: {response.token_usage.total_tokens if response.token_usage else 'N/A'}")
        print(f"Success: {response.success}\n")
    
    print("3. Exiting agent context")
    print("   ✓ MCP sessions closed\n")
    print("✓ All tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
