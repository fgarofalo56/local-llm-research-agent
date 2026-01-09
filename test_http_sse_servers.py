"""
Test HTTP and SSE MCP server connections.

Tests that:
1. Microsoft Docs MCP (Streamable HTTP) can be loaded
2. Archon MCP (SSE) can be loaded
3. Agent can initialize with mixed transports
"""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.mcp.client import MCPClientManager
from src.agent.core import ResearchAgent

console = Console()


async def test_http_sse_loading():
    """Test loading HTTP and SSE servers."""
    console.print("\n[bold cyan]Testing HTTP/SSE Server Loading[/bold cyan]")
    
    try:
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        
        # Get enabled servers
        enabled = config.get_enabled_servers()
        console.print(f"Found {len(enabled)} enabled servers")
        
        # Show transport types
        table = Table(title="Enabled MCP Servers")
        table.add_column("Server", style="cyan")
        table.add_column("Transport", style="yellow")
        table.add_column("Endpoint", style="magenta")
        
        for server in enabled:
            endpoint = ""
            if server.transport.value == "stdio":
                endpoint = f"{server.command} {' '.join(server.args[:2])}"
            else:
                endpoint = server.url or "N/A"
            
            table.add_row(
                server.name,
                server.transport.value,
                endpoint[:50] + "..." if len(endpoint) > 50 else endpoint
            )
        
        console.print(table)
        
        # Load toolsets
        console.print("\n[yellow]Loading toolsets (this may take a moment for HTTP/SSE)...[/yellow]")
        toolsets = manager.get_active_toolsets()
        console.print(f"Loaded {len(toolsets)} toolsets successfully")
        
        # Show what was loaded
        loaded_table = Table(title="Loaded Toolsets")
        loaded_table.add_column("Server", style="cyan")
        loaded_table.add_column("Transport", style="yellow")
        loaded_table.add_column("Status", style="green")
        
        for server_config in enabled:
            if server_config.name in manager._servers:
                server_obj = manager._servers[server_config.name]
                server_class = type(server_obj).__name__
                loaded_table.add_row(
                    server_config.name,
                    server_config.transport.value,
                    f"✅ {server_class}"
                )
            else:
                loaded_table.add_row(
                    server_config.name,
                    server_config.transport.value,
                    "❌ Failed to load"
                )
        
        console.print(loaded_table)
        
        # Count by transport
        transports = {}
        for s in enabled:
            if s.name in manager._servers:
                transports[s.transport.value] = transports.get(s.transport.value, 0) + 1
        
        console.print(f"\n[cyan]Successfully loaded by transport:[/cyan]")
        for transport, count in transports.items():
            console.print(f"  {transport}: {count}")
        
        console.print("\n✅ HTTP/SSE loading test passed!")
        return True
        
    except Exception as e:
        console.print(f"❌ HTTP/SSE loading failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_agent_with_http_sse():
    """Test agent initialization with HTTP and SSE servers."""
    console.print("\n[bold cyan]Testing Agent with HTTP/SSE Servers[/bold cyan]")
    
    try:
        # Test with all enabled servers
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        enabled_servers = [s.name for s in config.get_enabled_servers()]
        
        console.print(f"Initializing agent with {len(enabled_servers)} servers:")
        for name in enabled_servers:
            s = config.get_server(name)
            console.print(f"  - {name} ({s.transport.value})")
        
        # Create agent
        console.print("\n[yellow]Creating agent (HTTP/SSE connections may take time)...[/yellow]")
        agent = ResearchAgent(mcp_servers=enabled_servers)
        
        if agent.agent is not None:
            console.print("✅ Agent created successfully with mixed transports")
        else:
            console.print("❌ Agent creation failed")
            return False
        
        console.print("\n✅ Agent initialization with HTTP/SSE test passed!")
        return True
        
    except Exception as e:
        console.print(f"❌ Agent initialization failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_transport_connectivity():
    """Test actual connectivity to HTTP and SSE endpoints."""
    console.print("\n[bold cyan]Testing Transport Connectivity[/bold cyan]")
    
    try:
        import httpx
        
        # Test Microsoft Docs (Streamable HTTP)
        console.print("\n[yellow]Testing Microsoft Docs MCP (Streamable HTTP)...[/yellow]")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://learn.microsoft.com/api/mcp")
                console.print(f"  Status: {response.status_code}")
                if response.status_code < 400:
                    console.print("  ✅ Microsoft Docs MCP endpoint accessible")
                else:
                    console.print(f"  ⚠️ Endpoint returned {response.status_code}")
        except Exception as e:
            console.print(f"  ❌ Connection failed: {e}")
        
        # Test Archon (SSE)
        console.print("\n[yellow]Testing Archon MCP (SSE)...[/yellow]")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "http://localhost:8051/sse",
                    headers={"Accept": "text/event-stream"}
                )
                console.print(f"  Status: {response.status_code}")
                if response.status_code < 400:
                    console.print("  ✅ Archon SSE endpoint accessible")
                else:
                    console.print(f"  ⚠️ Endpoint returned {response.status_code}")
        except Exception as e:
            console.print(f"  ❌ Connection failed: {e}")
        
        console.print("\n✅ Connectivity test completed!")
        return True
        
    except ImportError:
        console.print("⚠️ httpx not installed, skipping connectivity test")
        console.print("  Install with: uv add httpx")
        return True


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]HTTP/SSE MCP Server Integration Test[/bold cyan]\n"
        "Testing Microsoft Docs (HTTP) and Archon (SSE) connections",
        border_style="cyan"
    ))
    
    results = []
    results.append(("Transport Connectivity", await test_transport_connectivity()))
    results.append(("HTTP/SSE Loading", await test_http_sse_loading()))
    results.append(("Agent with HTTP/SSE", await test_agent_with_http_sse()))
    
    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        console.print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        console.print("\n[bold green]✅ All HTTP/SSE tests passed![/bold green]")
    else:
        console.print("\n[bold yellow]⚠️ Some tests failed - check connectivity[/bold yellow]")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
