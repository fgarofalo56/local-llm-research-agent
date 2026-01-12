"""
Multi-MCP Server Example

Demonstrates how to use multiple MCP servers simultaneously. Shows:
- Loading multiple MCP servers (MSSQL, Analytics, custom)
- Agent selecting appropriate tools from different servers
- Combining data across MCP server capabilities
- Server management and status checking

Prerequisites:
1. Ollama running with a compatible model (qwen3:30b recommended)
2. Multiple MCP servers configured in mcp_config.json
3. SQL Server databases running (ports 1433, 1434)
4. Environment variables set in .env file
"""

import asyncio
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.research_agent import ResearchAgent, create_research_agent
from src.mcp.client import MCPClientManager
from src.utils.config import settings
from src.utils.logger import setup_logging


def show_mcp_servers() -> list[str]:
    """Display configured MCP servers and their status."""
    print("\n" + "=" * 60)
    print("Configured MCP Servers")
    print("=" * 60)

    manager = MCPClientManager()
    servers = manager.list_servers()
    enabled_servers = []

    print(f"\nFound {len(servers)} configured servers:\n")
    for server in servers:
        status = "[ENABLED]" if server.enabled else "[disabled]"
        print(f"  {status} {server.name}")
        print(f"         Type: {server.server_type}, Transport: {server.transport}")
        if server.description:
            print(f"         Description: {server.description}")
        if server.enabled:
            enabled_servers.append(server.name)
        print()

    return enabled_servers


async def demo_database_query(agent: ResearchAgent) -> None:
    """Use MSSQL MCP server to query database."""
    print("\n" + "=" * 60)
    print("DEMO: Database Query via MSSQL MCP")
    print("=" * 60)
    print("\nUsing the MSSQL MCP server tools to query the database.")
    print("-" * 60)

    async with agent:
        response = await agent.chat(
            "List all tables in the database and show me the total count "
            "of researchers grouped by department."
        )
        print(f"\n{response}")


async def demo_analytics_tools(agent: ResearchAgent) -> None:
    """Use Analytics MCP server for data analysis."""
    print("\n" + "=" * 60)
    print("DEMO: Analytics via Analytics MCP")
    print("=" * 60)
    print("\nUsing analytics-management or data-analytics MCP server tools.")
    print("-" * 60)

    async with agent:
        response = await agent.chat(
            "Can you show me the available analytics dashboards and widgets? "
            "If none exist, describe what analytics capabilities are available."
        )
        print(f"\n{response}")


async def demo_combined_workflow(agent: ResearchAgent) -> None:
    """Demonstrate using multiple MCP servers in one workflow."""
    print("\n" + "=" * 60)
    print("DEMO: Combined Multi-MCP Workflow")
    print("=" * 60)
    print("\nThis query may use tools from multiple MCP servers.")
    print("-" * 60)

    async with agent:
        # Query that might require multiple server capabilities
        response = await agent.chat(
            "I need a comprehensive overview: "
            "1. First, show me the database schema and key tables. "
            "2. Then, if analytics tools are available, create a summary dashboard. "
            "3. Finally, give me the top 5 researchers by publication count."
        )
        print(f"\n{response}")


async def demo_tool_selection(agent: ResearchAgent) -> None:
    """Show how agent intelligently selects tools from different servers."""
    print("\n" + "=" * 60)
    print("DEMO: Intelligent Tool Selection")
    print("=" * 60)
    print("\nThe agent automatically selects the appropriate MCP server tools.")
    print("-" * 60)

    queries = [
        ("Database exploration", "What tables exist in the database?"),
        ("Data query", "Show me all projects with budget > $100,000"),
        ("Statistical analysis", "Calculate the average salary by department"),
    ]

    async with agent:
        for query_type, query in queries:
            print(f"\n[{query_type}]")
            print(f"Query: {query}")
            response = await agent.chat(query)
            print(f"Response: {response[:500]}..." if len(response) > 500 else f"Response: {response}")


async def demo_server_specific_query(agent: ResearchAgent, server_name: str) -> None:
    """Query specifically targeting one MCP server."""
    print(f"\n" + "=" * 60)
    print(f"DEMO: Query targeting {server_name} server")
    print("=" * 60)
    print(f"\nDirectly using tools from the {server_name} MCP server.")
    print("-" * 60)

    async with agent:
        if "mssql" in server_name.lower():
            response = await agent.chat(
                "Using the SQL Server tools, describe the Researchers table schema "
                "and show me the first 5 records."
            )
        elif "analytics" in server_name.lower():
            response = await agent.chat(
                "Using the analytics tools, list available dashboard operations "
                "or statistical functions."
            )
        else:
            response = await agent.chat(
                f"List the available tools from the {server_name} MCP server."
            )
        print(f"\n{response}")


async def main():
    """Run multi-MCP server demonstrations."""
    setup_logging()

    print("=" * 60)
    print("Multi-MCP Server Example - Local LLM Research Agent")
    print("=" * 60)
    print(f"\nProvider: {settings.default_provider}")
    print(f"Model: {settings.default_model}")
    print("\nThis example shows how to use multiple MCP servers simultaneously.")

    # Show configured MCP servers
    enabled_servers = show_mcp_servers()

    if not enabled_servers:
        print("\nNo MCP servers are enabled!")
        print("Enable servers in mcp_config.json or use '/mcp enable <name>' in CLI")
        return

    print(f"\nCreating agent with {len(enabled_servers)} enabled servers...")
    print(f"Servers: {', '.join(enabled_servers)}")

    # Create agent with all enabled MCP servers
    agent = create_research_agent(
        readonly=True,
        mcp_servers=enabled_servers,
    )

    try:
        # Run demonstrations based on available servers
        if any("mssql" in s.lower() for s in enabled_servers):
            await demo_database_query(agent)

        if any("analytics" in s.lower() for s in enabled_servers):
            await demo_analytics_tools(agent)

        # Always run combined workflow and tool selection demos
        await demo_combined_workflow(agent)
        await demo_tool_selection(agent)

        # Demo with first available server
        if enabled_servers:
            await demo_server_specific_query(agent, enabled_servers[0])

        # Show session summary
        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)
        print(f"Total conversation turns: {agent.turn_count}")
        print(f"MCP servers used: {', '.join(enabled_servers)}")
        cache_stats = agent.get_cache_stats()
        print(f"Cache hits: {cache_stats.hits}")
        print(f"Cache misses: {cache_stats.misses}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. Your LLM provider is running (Ollama or Foundry Local)")
        print("2. MCP servers are configured in mcp_config.json")
        print("3. Required databases and services are accessible")
        print("4. Environment variables are set in .env file")
        raise


if __name__ == "__main__":
    asyncio.run(main())
