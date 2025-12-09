"""
Multi-Tool Example

Demonstrates how to use the research agent with multiple MCP tool calls
in a single conversation. Shows how the agent can:
- Chain multiple tool calls to answer complex questions
- Use different tools (list_tables, describe_table, read_data)
- Build context across queries
- Handle multi-step analytical tasks

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


async def demo_exploratory_analysis(agent: ResearchAgent) -> None:
    """Demonstrate exploratory analysis requiring multiple tool calls."""
    print("\n" + "=" * 60)
    print("DEMO: Exploratory Analysis")
    print("=" * 60)
    print("\nThis query requires the agent to:")
    print("1. List tables to understand the database structure")
    print("2. Examine table schemas")
    print("3. Query data to answer the question")
    print("-" * 60)

    response = await agent.chat(
        "I'm new to this database. Can you explore the schema and tell me "
        "what kind of research data is being tracked? Include a summary of "
        "the main entities and their relationships."
    )
    print(f"\n{response}")


async def demo_cross_table_query(agent: ResearchAgent) -> None:
    """Demonstrate a query that requires joining multiple tables."""
    print("\n" + "=" * 60)
    print("DEMO: Cross-Table Query")
    print("=" * 60)
    print("\nThis query requires combining data from multiple tables.")
    print("-" * 60)

    response = await agent.chat(
        "Show me a report of departments with their total project count, "
        "total budget, and number of researchers. Rank them by total budget."
    )
    print(f"\n{response}")


async def demo_data_validation(agent: ResearchAgent) -> None:
    """Demonstrate data validation across tables."""
    print("\n" + "=" * 60)
    print("DEMO: Data Validation")
    print("=" * 60)
    print("\nThis query checks data consistency across tables.")
    print("-" * 60)

    response = await agent.chat(
        "Check the data quality: Are there any projects without a lead researcher? "
        "Any researchers not assigned to any project? "
        "Summarize any data integrity issues you find."
    )
    print(f"\n{response}")


async def demo_analytical_workflow(agent: ResearchAgent) -> None:
    """Demonstrate a multi-step analytical workflow."""
    print("\n" + "=" * 60)
    print("DEMO: Multi-Step Analytical Workflow")
    print("=" * 60)
    print("\nThis demonstrates maintaining context across multiple queries.")
    print("-" * 60)

    # Step 1: Identify top performers
    print("\n[Step 1: Identify research areas]")
    response1 = await agent.chat(
        "What are the different research areas/departments in the database? "
        "List them with their department codes."
    )
    print(f"\n{response1}")

    # Step 2: Deep dive into one area
    print("\n[Step 2: Deep dive into top department]")
    response2 = await agent.chat(
        "Now focus on the department with the highest budget. "
        "What projects are they working on and who leads them?"
    )
    print(f"\n{response2}")

    # Step 3: Analyze funding
    print("\n[Step 3: Analyze funding patterns]")
    response3 = await agent.chat(
        "For that same department, analyze the funding sources. "
        "What grants do they have and what's the status of each?"
    )
    print(f"\n{response3}")


async def demo_comparison_query(agent: ResearchAgent) -> None:
    """Demonstrate comparing data across categories."""
    print("\n" + "=" * 60)
    print("DEMO: Comparison Query")
    print("=" * 60)
    print("\nComparing metrics across categories requires multiple queries.")
    print("-" * 60)

    response = await agent.chat(
        "Compare the productivity across departments: "
        "Which department has the highest publication count per researcher? "
        "Show the department name, number of researchers, total publications, "
        "and publications per person."
    )
    print(f"\n{response}")


async def demo_trend_analysis(agent: ResearchAgent) -> None:
    """Demonstrate temporal trend analysis."""
    print("\n" + "=" * 60)
    print("DEMO: Trend Analysis")
    print("=" * 60)
    print("\nAnalyzing trends over time with multiple tool calls.")
    print("-" * 60)

    response = await agent.chat(
        "Analyze project trends: How many projects were started each year? "
        "What's the trend in project budgets over time? "
        "Are projects getting larger or smaller in scope?"
    )
    print(f"\n{response}")


async def demo_complex_report(agent: ResearchAgent) -> None:
    """Demonstrate generating a complex report."""
    print("\n" + "=" * 60)
    print("DEMO: Complex Report Generation")
    print("=" * 60)
    print("\nGenerating a comprehensive report requires many tool calls.")
    print("-" * 60)

    response = await agent.chat(
        "Generate an executive summary report that includes:\n"
        "1. Total number of researchers, projects, and publications\n"
        "2. Budget overview: total allocated vs spent\n"
        "3. Top 3 most productive researchers by publications\n"
        "4. Projects that are over budget\n"
        "5. Any projects past their end date but not marked complete\n"
        "Format this as a structured report."
    )
    print(f"\n{response}")


async def main():
    """Run all multi-tool demonstrations."""
    setup_logging()

    print("=" * 60)
    print("Multi-Tool Example - Local LLM Research Agent")
    print("=" * 60)
    print(f"\nProvider: {settings.default_provider}")
    print(f"Model: {settings.default_model}")
    print(f"Database: {settings.mcp_mssql_database}")
    print("\nThis example shows how the agent chains multiple MCP tool calls")
    print("to answer complex analytical questions.")

    # Create agent in read-only mode for safety
    agent = create_research_agent(readonly=True)

    try:
        # Run demonstrations
        await demo_exploratory_analysis(agent)
        await demo_cross_table_query(agent)
        await demo_data_validation(agent)
        await demo_analytical_workflow(agent)
        await demo_comparison_query(agent)
        await demo_trend_analysis(agent)
        await demo_complex_report(agent)

        # Show session statistics
        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)
        print(f"Total conversation turns: {agent.turn_count}")
        cache_stats = agent.get_cache_stats()
        print(f"Cache hits: {cache_stats.hits}")
        print(f"Cache misses: {cache_stats.misses}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. Your LLM provider is running (Ollama or Foundry Local)")
        print("2. MSSQL MCP Server is configured correctly")
        print("3. SQL Server is accessible with the ResearchAnalytics database")
        print("4. Environment variables are set in .env file")
        raise


if __name__ == "__main__":
    asyncio.run(main())
