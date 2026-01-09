"""
Test script for MCP transport types.

Verifies that:
1. Configuration model supports all three transport types
2. MCPClientManager can load servers with different transports
3. Validation works correctly for each transport type
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.mcp.client import MCPClientManager
from src.mcp.config import TransportType, MCPServerType, MCPServerConfig

console = Console()


def test_config_models():
    """Test that config models support all transport types."""
    console.print("\n[bold cyan]Testing Configuration Models[/bold cyan]")
    
    # Test stdio transport
    try:
        stdio_config = MCPServerConfig(
            name="test_stdio",
            server_type=MCPServerType.CUSTOM,
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
            env={"KEY": "value"},
        )
        console.print(f"✅ Stdio transport config: {stdio_config.name}")
    except Exception as e:
        console.print(f"❌ Stdio transport failed: {e}")
        return False
    
    # Test streamable HTTP transport
    try:
        http_config = MCPServerConfig(
            name="test_http",
            server_type=MCPServerType.CUSTOM,
            transport=TransportType.STREAMABLE_HTTP,
            url="http://localhost:8000/mcp",
            headers={"Authorization": "Bearer token"},
        )
        console.print(f"✅ Streamable HTTP transport config: {http_config.name}")
    except Exception as e:
        console.print(f"❌ Streamable HTTP transport failed: {e}")
        return False
    
    # Test SSE transport
    try:
        sse_config = MCPServerConfig(
            name="test_sse",
            server_type=MCPServerType.CUSTOM,
            transport=TransportType.SSE,
            url="http://localhost:8000/sse",
            headers={"X-API-Key": "key"},
        )
        console.print(f"✅ SSE transport config: {sse_config.name}")
    except Exception as e:
        console.print(f"❌ SSE transport failed: {e}")
        return False
    
    # Test validation: stdio without command should fail
    try:
        bad_stdio = MCPServerConfig(
            name="bad_stdio",
            server_type=MCPServerType.CUSTOM,
            transport=TransportType.STDIO,
            url="http://localhost:8000",  # Wrong field
        )
        console.print(f"❌ Validation failed: stdio without command should error")
        return False
    except ValueError as e:
        console.print(f"✅ Validation working: {str(e)[:50]}...")
    
    # Test validation: HTTP without URL should fail
    try:
        bad_http = MCPServerConfig(
            name="bad_http",
            server_type=MCPServerType.CUSTOM,
            transport=TransportType.STREAMABLE_HTTP,
            command="node",  # Wrong field
        )
        console.print(f"❌ Validation failed: HTTP without URL should error")
        return False
    except ValueError as e:
        console.print(f"✅ Validation working: {str(e)[:50]}...")
    
    console.print("\n✅ All config model tests passed!")
    return True


def test_mcp_config_file():
    """Test loading actual mcp_config.json with transport fields."""
    console.print("\n[bold cyan]Testing MCP Config File[/bold cyan]")
    
    try:
        manager = MCPClientManager("mcp_config.json")
        config = manager.load_config()
        
        # Check all servers have transport field
        table = Table(title="MCP Servers Configuration")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Transport", style="yellow")
        table.add_column("Enabled", style="green")
        
        for name, server in config.mcpServers.items():
            transport_icon = {
                TransportType.STDIO: "🔧",
                TransportType.STREAMABLE_HTTP: "🌐",
                TransportType.SSE: "📡",
            }.get(server.transport, "❓")
            
            table.add_row(
                name,
                server.server_type.value,
                f"{transport_icon} {server.transport.value}",
                "✅" if server.enabled else "❌",
            )
        
        console.print(table)
        
        # Count transports
        transports = {}
        for server in config.mcpServers.values():
            transports[server.transport] = transports.get(server.transport, 0) + 1
        
        console.print(f"\nTransport counts:")
        for transport, count in transports.items():
            console.print(f"  {transport.value}: {count}")
        
        console.print("\n✅ Config file loaded successfully!")
        return True
        
    except Exception as e:
        console.print(f"❌ Failed to load config: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


def test_backward_compatibility():
    """Test that legacy configs without transport field work."""
    console.print("\n[bold cyan]Testing Backward Compatibility[/bold cyan]")
    
    # Legacy config with command (should auto-detect stdio)
    legacy_data = {
        "name": "legacy_stdio",
        "server_type": "custom",
        "command": "node",
        "args": ["server.js"],
        "env": {},
    }
    
    try:
        config = MCPServerConfig.from_dict(legacy_data)
        if config.transport == TransportType.STDIO:
            console.print(f"✅ Legacy stdio auto-detected: {config.name}")
        else:
            console.print(f"❌ Expected stdio, got: {config.transport}")
            return False
    except Exception as e:
        console.print(f"❌ Legacy stdio failed: {e}")
        return False
    
    # Legacy config with URL (should auto-detect streamable_http)
    legacy_http_data = {
        "name": "legacy_http",
        "server_type": "custom",
        "url": "http://localhost:8000/mcp",
        "headers": {},
    }
    
    try:
        config = MCPServerConfig.from_dict(legacy_http_data)
        if config.transport == TransportType.STREAMABLE_HTTP:
            console.print(f"✅ Legacy HTTP auto-detected: {config.name}")
        else:
            console.print(f"❌ Expected streamable_http, got: {config.transport}")
            return False
    except Exception as e:
        console.print(f"❌ Legacy HTTP failed: {e}")
        return False
    
    console.print("\n✅ Backward compatibility tests passed!")
    return True


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]MCP Transport Types Test Suite[/bold cyan]\n"
        "Testing support for stdio, streamable_http, and sse transports",
        border_style="cyan"
    ))
    
    results = []
    results.append(("Config Models", test_config_models()))
    results.append(("MCP Config File", test_mcp_config_file()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        console.print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        console.print("\n[bold green]✅ All tests passed![/bold green]")
    else:
        console.print("\n[bold red]❌ Some tests failed![/bold red]")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
