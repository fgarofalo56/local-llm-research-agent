"""
SQL Query Example

Demonstrates how to use the research agent to query SQL Server data.
Shows various query patterns including:
- Listing tables
- Describing table schemas
- Running data queries
- Aggregation queries
- Filtering and sorting

Prerequisites:
1. Ollama or Foundry Local running with a compatible model
2. MSSQL MCP Server setup and configured
3. SQL Server database available (e.g., ResearchAnalytics)
4. Environment variables set in .env file
"""

import asyncio
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.research_agent import ResearchAgent, create_research_agent
from src.utils.config import settings
from src.utils.logger import setup_logging


async def demo_list_tables(agent: ResearchAgent) -> None:
    """Demonstrate listing available tables."""
    print("\n" + "=" * 60)
    print("DEMO: List Available Tables")
    print("=" * 60)

    response = await agent.chat("What tables are available in the database?")
    print(f"\n{response}")


async def demo_describe_table(agent: ResearchAgent) -> None:
    """Demonstrate describing a table schema."""
    print("\n" + "=" * 60)
    print("DEMO: Describe Table Schema")
    print("=" * 60)

    response = await agent.chat(
        "Describe the schema of the Researchers table. "
        "What columns does it have and what are their types?"
    )
    print(f"\n{response}")


async def demo_simple_query(agent: ResearchAgent) -> None:
    """Demonstrate a simple SELECT query."""
    print("\n" + "=" * 60)
    print("DEMO: Simple SELECT Query")
    print("=" * 60)

    response = await agent.chat(
        "Show me the first 5 researchers in the database with their names and departments."
    )
    print(f"\n{response}")


async def demo_aggregation_query(agent: ResearchAgent) -> None:
    """Demonstrate an aggregation query."""
    print("\n" + "=" * 60)
    print("DEMO: Aggregation Query")
    print("=" * 60)

    response = await agent.chat(
        "How many researchers are in each department? Show the count per department."
    )
    print(f"\n{response}")


async def demo_filtered_query(agent: ResearchAgent) -> None:
    """Demonstrate a filtered query."""
    print("\n" + "=" * 60)
    print("DEMO: Filtered Query")
    print("=" * 60)

    response = await agent.chat(
        "List all active projects with a budget greater than $100,000. "
        "Show project name, budget, and status."
    )
    print(f"\n{response}")


async def demo_join_query(agent: ResearchAgent) -> None:
    """Demonstrate a query with table joins."""
    print("\n" + "=" * 60)
    print("DEMO: Join Query")
    print("=" * 60)

    response = await agent.chat(
        "Show researchers along with the projects they lead. "
        "Include researcher name, project name, and project status."
    )
    print(f"\n{response}")


async def demo_complex_analysis(agent: ResearchAgent) -> None:
    """Demonstrate a complex analytical query."""
    print("\n" + "=" * 60)
    print("DEMO: Complex Analysis")
    print("=" * 60)

    response = await agent.chat(
        "What are the top 3 departments by total project budget? "
        "Include the number of projects and total budget for each department."
    )
    print(f"\n{response}")


async def main():
    """Run all SQL query demonstrations."""
    setup_logging()

    print("=" * 60)
    print("SQL Query Example - Local LLM Research Agent")
    print("=" * 60)
    print(f"\nProvider: {settings.default_provider}")
    print(f"Model: {settings.default_model}")
    print(f"Database: {settings.mcp_mssql_database}")

    # Create agent in read-only mode for safety
    agent = create_research_agent(readonly=True)

    try:
        # Run demonstrations
        await demo_list_tables(agent)
        await demo_describe_table(agent)
        await demo_simple_query(agent)
        await demo_aggregation_query(agent)
        await demo_filtered_query(agent)
        await demo_join_query(agent)
        await demo_complex_analysis(agent)

        # Show conversation summary
        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)
        print(f"Total turns: {agent.turn_count}")
        print(f"Cache stats: {agent.get_cache_stats()}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. Your LLM provider is running (Ollama or Foundry Local)")
        print("2. MSSQL MCP Server is configured correctly")
        print("3. SQL Server is accessible")
        print("4. Environment variables are set in .env file")
        raise


if __name__ == "__main__":
    asyncio.run(main())
