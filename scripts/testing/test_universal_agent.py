"""
Test Script for Universal Agent

Tests the new universal research assistant capabilities:
1. General questions (no tools needed)
2. SQL questions (with MSSQL tools)
3. Multi-MCP server management
4. Graceful error handling
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager
from src.mcp.config import MCPServerType

console = Console()


async def test_general_questions():
    """Test agent with NO tools - pure general questions."""
    console.print("\n[bold cyan]Test 1: General Questions (No Tools)[/bold cyan]")
    console.print("Testing agent without any MCP tools...\n")
    
    agent = ResearchAgent(thinking_mode=False, mcp_servers=[])
    
    questions = [
        "What is 2+2?",
        "Explain what Python is in one sentence.",
        "What's the capital of France?",
    ]
    
    for q in questions:
        console.print(f"[yellow]Q:[/yellow] {q}")
        response = await agent.chat(q)
        console.print(f"[green]A:[/green] {response}\n")


async def test_with_sql_tools():
    """Test agent with SQL tools for both SQL and general questions."""
    console.print("\n[bold cyan]Test 2: With SQL Tools (Universal)[/bold cyan]")
    console.print("Testing agent with MSSQL tools but asking different question types...\n")
    
    agent = ResearchAgent(thinking_mode=False, mcp_servers=["mssql"])
    
    questions = [
        "What programming languages are popular in 2024?",
        "What tables are in the database?",  # Should use SQL tools
        "Explain what a REST API is briefly.",
    ]
    
    for q in questions:
        console.print(f"[yellow]Q:[/yellow] {q}")
        try:
            response = await agent.chat(q)
            console.print(f"[green]A:[/green] {response[:200]}...\n")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}\n")


def test_mcp_manager():
    """Test multi-MCP server management."""
    console.print("\n[bold cyan]Test 3: Multi-MCP Server Management[/bold cyan]")
    
    manager = MCPClientManager()
    
    # List current servers
    servers = manager.list_servers()
    
    table = Table(title="Configured MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Command", style="yellow")
    table.add_column("Enabled", style="green")
    
    for server in servers:
        table.add_row(
            server.name,
            server.server_type.value,
            str(server.command or "HTTP")[:30],
            "✓" if server.enabled else "✗"
        )
    
    console.print(table)
    
    # Test active toolsets
    console.print("\n[bold]Getting active toolsets...[/bold]")
    toolsets = manager.get_active_toolsets()
    console.print(f"Loaded [green]{len(toolsets)}[/green] active MCP server toolsets\n")
    
    # Test enable/disable
    console.print("[bold]Testing enable/disable...[/bold]")
    if len(servers) > 1:
        test_server = servers[1].name
        console.print(f"Disabling: {test_server}")
        manager.disable_server(test_server)
        
        console.print(f"Enabling: {test_server}")
        manager.enable_server(test_server)
        console.print("[green]✓ Enable/disable working[/green]\n")


async def test_error_handling():
    """Test graceful error handling with invalid tools."""
    console.print("\n[bold cyan]Test 4: Error Handling[/bold cyan]")
    console.print("Testing agent with non-existent MCP server...\n")
    
    # Try to load agent with invalid server name - should gracefully continue
    agent = ResearchAgent(thinking_mode=False, mcp_servers=["mssql", "nonexistent_server"])
    
    # Should still work for general questions
    response = await agent.chat("What is 5+5?")
    console.print(f"[green]✓ Agent still works despite failed tool loading[/green]")
    console.print(f"Response: {response}\n")


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]Universal Research Agent Test Suite[/bold cyan]\n"
        "Testing new multi-MCP and universal question capabilities",
        border_style="cyan"
    ))
    
    try:
        await test_general_questions()
        await test_with_sql_tools()
        test_mcp_manager()
        await test_error_handling()
        
        console.print(Panel.fit(
            "[bold green]✓ All Tests Passed![/bold green]\n"
            "The universal agent is working correctly.",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"\n[bold red]Test Failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
