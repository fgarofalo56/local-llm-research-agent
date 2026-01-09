#!/usr/bin/env python3
"""
Test agent tool loading and visibility.
"""
import asyncio
from rich.console import Console
from rich.table import Table
from src.agent.core import ResearchAgent
from src.mcp.client import MCPClientManager

console = Console()

async def main():
    console.print("[bold cyan]Testing Agent Tool Loading[/]\n")
    
    # Step 1: Check enabled servers
    console.print("[yellow]Step 1: Checking enabled MCP servers...[/]")
    mcp_manager = MCPClientManager()
    enabled_servers = [s.name for s in mcp_manager.list_servers() if s.enabled]
    console.print(f"Enabled servers: {enabled_servers}\n")
    
    # Step 2: Create agent with all enabled servers
    console.print("[yellow]Step 2: Creating ResearchAgent...[/]")
    agent = ResearchAgent(
        provider_type="ollama",
        model_name="qwen3:30b",
        readonly=True,
        mcp_servers=enabled_servers,
    )
    console.print(f"Agent created with {len(agent._enabled_mcp_servers)} servers\n")
    
    # Step 3: Check loaded toolsets
    console.print("[yellow]Step 3: Checking loaded toolsets...[/]")
    console.print(f"Active toolsets count: {len(agent._active_toolsets)}")
    for i, toolset in enumerate(agent._active_toolsets, 1):
        console.print(f"  {i}. {type(toolset).__name__}")
    console.print()
    
    # Step 4: Check Pydantic AI agent
    console.print("[yellow]Step 4: Checking Pydantic AI agent...[/]")
    console.print(f"Agent has 'agent' attribute: {hasattr(agent, 'agent')}")
    console.print(f"Agent.agent type: {type(agent.agent).__name__}")
    
    # Check if Pydantic AI Agent has tools
    if hasattr(agent.agent, '_function_tools'):
        console.print(f"Function tools: {len(agent.agent._function_tools)}")
    
    console.print()
    
    # Step 5: Check Pydantic AI agent toolsets
    console.print("[yellow]Step 5: Checking Pydantic AI agent toolsets...[/]")
    if hasattr(agent.agent, '_function_toolsets'):
        console.print(f"Toolsets registered: {len(agent.agent._function_toolsets)}")
        for i, toolset in enumerate(agent.agent._function_toolsets, 1):
            console.print(f"  {i}. {type(toolset).__name__}")
    else:
        console.print("[yellow]_function_toolsets attribute not found[/]")
    console.print()
    
    # Step 6: Try to list tools from the agent
    console.print("[yellow]Step 6: Attempting to query agent about tools...[/]")
    try:
        response = await agent.chat("What tools do you have access to? List them specifically by name.")
        console.print(f"[green]Agent response:[/]\n{response}\n")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]\n")
    
    console.print("[bold green]✓ Test complete[/]")

if __name__ == "__main__":
    asyncio.run(main())
