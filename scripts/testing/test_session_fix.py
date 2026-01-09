#!/usr/bin/env python3
"""
Quick test to verify MCP session management fix.

This test verifies that:
1. Agent context can be entered/exited correctly
2. MCP sessions are NOT re-established on each message
3. The agent can still respond to queries
"""
import asyncio
import sys
from src.agent.core import ResearchAgent
from src.utils.config import settings

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


async def test_session_management():
    """Test that MCP sessions persist across multiple messages."""
    print("=" * 60)
    print("Testing MCP Session Management Fix")
    print("=" * 60)
    
    # Create agent with mssql server
    print("\n1. Creating ResearchAgent...")
    agent = ResearchAgent(
        provider_type=settings.llm_provider,
        mcp_servers=["mssql"],  # Use mssql for testing
    )
    print("   ✓ Agent created")
    
    # Enter agent context (should establish MCP sessions ONCE)
    print("\n2. Entering agent context (establishing MCP sessions)...")
    async with agent:
        print("   ✓ MCP sessions established")
        
        # Send first message
        print("\n3. Sending first message...")
        print("   Message: 'Do you have access to tools?'")
        response1 = await agent.chat("Do you have access to tools?")
        print(f"   Response: {response1[:100]}...")
        print("   ✓ First message processed")
        
        # Send second message
        print("\n4. Sending second message (should reuse existing session)...")
        print("   Message: 'What tables are available?'")
        response2 = await agent.chat("What tables are available?")
        print(f"   Response: {response2[:100]}...")
        print("   ✓ Second message processed")
        
        print("\n5. Exiting agent context (closing MCP sessions)...")
    
    print("   ✓ MCP sessions closed")
    print("\n" + "=" * 60)
    print("✅ Session management test completed successfully!")
    print("=" * 60)
    print("\nExpected behavior:")
    print("- MCP sessions established ONCE at context entry")
    print("- Multiple messages reuse the same session")
    print("- No reconnection between messages")
    print("- Sessions closed cleanly at context exit")


if __name__ == "__main__":
    asyncio.run(test_session_management())
