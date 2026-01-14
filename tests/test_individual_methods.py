"""
Individual Method Tests
========================

Test each chat method in isolation.
Run individual tests with: python -c "from tests.test_individual_methods import *; asyncio.run(test_chat())"
"""

import asyncio
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager


async def test_chat():
    """Test Method 1: chat() with caching."""
    print("\n=== Testing chat() ===\n")
    
    mcp_manager = MCPClientManager()
    agent = ResearchAgent(mcp_servers=["mssql"])
    
    async with agent:
        # First call
        print("Call 1: Fresh query")
        response1 = await agent.chat("What tables are in the database?")
        print(f"Response length: {len(response1)} chars")
        
        # Second call (cached)
        print("\nCall 2: Same query (should be cached)")
        response2 = await agent.chat("What tables are in the database?")
        print(f"Response length: {len(response2)} chars")
        print(f"Responses match: {response1 == response2}")
        
        # Third call (different query)
        print("\nCall 3: Different query")
        response3 = await agent.chat("How many researchers are there?")
        print(f"Response length: {len(response3)} chars")
    
    print("\n✓ Test complete")


async def test_chat_stream():
    """Test Method 2: chat_stream() streaming."""
    print("\n=== Testing chat_stream() ===\n")
    
    mcp_manager = MCPClientManager()
    agent = ResearchAgent(mcp_servers=["mssql"])
    
    async with agent:
        print("Streaming query results:\n")
        print("-" * 60)
        
        chunk_count = 0
        async for chunk in agent.chat_stream("List all departments"):
            print(chunk, end="", flush=True)
            chunk_count += 1
        
        print()
        print("-" * 60)
        
        stats = agent.get_last_response_stats()
        print(f"\nChunks received: {chunk_count}")
        print(f"Stats: {stats}")
    
    print("\n✓ Test complete")


async def test_chat_with_details():
    """Test Method 3: chat_with_details() metadata."""
    print("\n=== Testing chat_with_details() ===\n")
    
    mcp_manager = MCPClientManager()
    agent = ResearchAgent(mcp_servers=["mssql"])
    
    async with agent:
        print("Querying with full metadata...\n")
        
        response = await agent.chat_with_details("Show me 5 projects")
        
        print(f"Success: {response.success}")
        print(f"Model: {response.model}")
        print(f"Duration: {response.duration_ms:.2f}ms")
        print(f"Content length: {len(response.content)} chars")
        print(f"Tool calls: {len(response.tool_calls)}")
        
        if response.token_usage:
            print(f"Tokens - Input: {response.token_usage.input_tokens}, "
                  f"Output: {response.token_usage.output_tokens}, "
                  f"Total: {response.token_usage.total_tokens}")
        
        if response.error:
            print(f"Error: {response.error}")
        
        print(f"\nContent preview:")
        print(response.content[:200] + "..." if len(response.content) > 200 else response.content)
    
    print("\n✓ Test complete")


async def test_all():
    """Run all three tests sequentially."""
    await test_chat()
    await test_chat_stream()
    await test_chat_with_details()


if __name__ == "__main__":
    # Run specific test or all
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "chat":
            asyncio.run(test_chat())
        elif test_name == "stream":
            asyncio.run(test_chat_stream())
        elif test_name == "details":
            asyncio.run(test_chat_with_details())
        else:
            print(f"Unknown test: {test_name}")
            print("Usage: python test_individual_methods.py [chat|stream|details]")
    else:
        # Run all tests
        asyncio.run(test_all())
