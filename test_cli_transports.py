"""
Test CLI with transport types.

Verifies that the CLI can load and initialize servers with different transport types.
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.mcp.client import MCPClientManager
from src.agent.core import ResearchAgent

console = Console()


async def test_mcp_loading():
    """Test that MCP client manager loads servers with correct transports."""
    console.print("\n[bold cyan]Testing MCP Client Manager[/bold cyan]")
    
    try:
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        
        # Get enabled servers
        enabled = config.get_enabled_servers()
        console.print(f"Found {len(enabled)} enabled servers")
        
        # Load toolsets
        toolsets = manager.get_active_toolsets()
        console.print(f"Loaded {len(toolsets)} toolsets")
        
        # Display what was loaded
        table = Table(title="Loaded MCP Toolsets")
        table.add_column("Server", style="cyan")
        table.add_column("Transport", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        
        for server_config in enabled:
            if server_config.name in manager._servers:
                server_obj = manager._servers[server_config.name]
                server_class = type(server_obj).__name__
                table.add_row(
                    server_config.name,
                    server_config.transport.value,
                    server_class,
                    "✅ Loaded"
                )
            else:
                table.add_row(
                    server_config.name,
                    server_config.transport.value,
                    "N/A",
                    "❌ Failed"
                )
        
        console.print(table)
        
        # Verify correct classes are used
        for server_config in enabled:
            if server_config.name in manager._servers:
                server_obj = manager._servers[server_config.name]
                server_class = type(server_obj).__name__
                
                expected_class = {
                    "stdio": "MCPServerStdio",
                    "streamable_http": "MCPServerStreamableHTTP",
                    "sse": "MCPServerSSE",
                }.get(server_config.transport.value)
                
                if server_class == expected_class:
                    console.print(f"✅ {server_config.name}: correct class {server_class}")
                else:
                    console.print(f"❌ {server_config.name}: expected {expected_class}, got {server_class}")
                    return False
        
        console.print("\n✅ MCP loading test passed!")
        return True
        
    except Exception as e:
        console.print(f"❌ MCP loading failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_agent_initialization():
    """Test that agent initializes with mixed transport servers."""
    console.print("\n[bold cyan]Testing Agent Initialization[/bold cyan]")
    
    try:
        # Load enabled servers
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        enabled_servers = [s.name for s in config.get_enabled_servers()]
        
        console.print(f"Initializing agent with servers: {enabled_servers}")
        
        # Create agent (this will load MCP servers)
        agent = ResearchAgent(mcp_servers=enabled_servers)
        
        # Agent should be created successfully
        if agent.agent is not None:
            console.print(f"✅ Agent created successfully")
        else:
            console.print(f"❌ Agent was not created")
            return False
        
        # Verify agent has the correct model
        if hasattr(agent, 'model'):
            console.print(f"✅ Agent has model configured")
        else:
            console.print(f"❌ Agent missing model configuration")
            return False
        
        console.print("\n✅ Agent initialization test passed!")
        return True
        
    except Exception as e:
        console.print(f"❌ Agent initialization failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_system_prompt_generation():
    """Test that system prompt includes MCP server info."""
    console.print("\n[bold cyan]Testing System Prompt Generation[/bold cyan]")
    
    try:
        from src.agent.prompts import format_mcp_servers_info, get_system_prompt
        
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        enabled_servers = [s.name for s in config.get_enabled_servers()]
        
        # Generate MCP server info
        mcp_info = format_mcp_servers_info(enabled_servers)
        console.print(f"\n[dim]MCP Server Info (first 300 chars):[/dim]")
        console.print(f"[dim]{mcp_info[:300]}...[/dim]")
        
        # Get system prompt
        prompt = get_system_prompt(mcp_servers_info=mcp_info)
        
        # Verify MCP info is in prompt
        if mcp_info in prompt:
            console.print("✅ MCP server info included in system prompt")
        else:
            console.print("❌ MCP server info NOT in system prompt")
            return False
        
        # Verify server names are in prompt
        for server_name in enabled_servers:
            if server_name in prompt:
                console.print(f"✅ Found '{server_name}' in system prompt")
            else:
                console.print(f"⚠️ '{server_name}' not found in system prompt")
        
        console.print("\n✅ System prompt generation test passed!")
        return True
        
    except Exception as e:
        console.print(f"❌ System prompt test failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]CLI Transport Types Integration Test[/bold cyan]\n"
        "Testing CLI with stdio and HTTP transport servers",
        border_style="cyan"
    ))
    
    results = []
    results.append(("MCP Loading", await test_mcp_loading()))
    results.append(("Agent Initialization", await test_agent_initialization()))
    results.append(("System Prompt Generation", await test_system_prompt_generation()))
    
    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        console.print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        console.print("\n[bold green]✅ All CLI transport tests passed![/bold green]")
    else:
        console.print("\n[bold red]❌ Some CLI tests failed![/bold red]")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
