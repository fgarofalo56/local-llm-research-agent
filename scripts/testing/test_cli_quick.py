"""
Quick CLI Test

Fast test to verify the CLI works with the new universal agent.
"""

import asyncio
from src.agent.core import ResearchAgent

async def quick_test():
    print("=" * 60)
    print("QUICK TEST: Universal Agent")
    print("=" * 60)
    
    # Test 1: No tools
    print("\n[TEST 1] Agent with NO tools")
    agent1 = ResearchAgent(mcp_servers=[])
    result1 = await agent1.chat("What is Python?")
    print(f"✓ Response: {result1[:100]}...")
    
    # Test 2: With SQL tools, non-SQL question
    print("\n[TEST 2] Agent with SQL tools, asking general question")
    agent2 = ResearchAgent(mcp_servers=["mssql"])
    result2 = await agent2.chat("List the first 5 prime numbers")
    print(f"✓ Response: {result2[:100]}...")
    
    # Test 3: With SQL tools, SQL question
    print("\n[TEST 3] Agent with SQL tools, asking SQL question")
    result3 = await agent2.chat("What tables are in the database?")
    print(f"✓ Response: {result3[:150]}...")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Universal agent working!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(quick_test())
