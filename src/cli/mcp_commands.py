"""
MCP Command Handlers for CLI

Interactive commands for managing MCP servers from the CLI.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from src.cli.theme import COLORS, Icons, styled_divider
from src.mcp.client import MCPClientManager
from src.mcp.config import (
    BRAVE_SEARCH_TEMPLATE,
    MSSQL_SERVER_TEMPLATE,
    MCPServerConfig,
    MCPServerType,
    TransportType,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_mcp_table() -> Table:
    """Create styled table for MCP servers."""
    table = Table(show_header=True, header_style=f"bold {COLORS['primary']}", border_style=COLORS["gray_600"])
    table.add_column("Name", style=COLORS["primary"], no_wrap=True)
    table.add_column("Type", style=COLORS["accent"])
    table.add_column("Status", style=COLORS["white"])
    table.add_column("Command", style=COLORS["gray_400"], max_width=30)
    return table


def handle_mcp_list(console: Console, manager: MCPClientManager) -> None:
    """Handle /mcp list - Show all configured servers."""
    servers = manager.list_servers()

    if not servers:
        console.print()
        console.print(f"[{COLORS['warning']}]{Icons.INFO} No MCP servers configured[/]")
        console.print(f"[{COLORS['gray_400']}]Use [bold]/mcp add[/bold] to add a server[/]")
        return

    console.print()
    console.print(Panel.fit(
        f"[bold {COLORS['primary']}]{Icons.DATABASE} MCP Servers[/bold {COLORS['primary']}]",
        border_style=COLORS["primary"]
    ))
    console.print()

    table = create_mcp_table()

    for server in servers:
        # Status indicator
        status = Text()
        if server.enabled:
            status.append(f"{Icons.CHECK} ", style=COLORS["success"])
            status.append("Enabled", style=COLORS["success"])
        else:
            status.append(f"{Icons.CROSS} ", style=COLORS["gray_400"])
            status.append("Disabled", style=COLORS["gray_400"])

        # Command display
        cmd_display = server.command or "HTTP"
        if server.command and len(server.args) > 0:
            cmd_display = f"{server.command} {server.args[0]}"

        table.add_row(
            server.name,
            server.server_type.value,
            status,
            cmd_display[:30]
        )

    console.print(table)

    # Summary
    enabled_count = sum(1 for s in servers if s.enabled)
    console.print()
    console.print(
        f"[{COLORS['gray_400']}]{Icons.INFO} Total: {len(servers)}, "
        f"Enabled: [{COLORS['success']}]{enabled_count}[/], "
        f"Disabled: [{COLORS['gray_400']}]{len(servers) - enabled_count}[/][/]"
    )


def handle_mcp_status(console: Console, manager: MCPClientManager, server_name: str) -> None:
    """Handle /mcp status <name> - Show detailed server status."""
    servers = manager.list_servers()
    server = next((s for s in servers if s.name == server_name), None)

    if not server:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Server not found: {server_name}[/]")
        return

    console.print()
    console.print(Panel.fit(
        f"[bold {COLORS['primary']}]{Icons.DATABASE} {server.name}[/bold {COLORS['primary']}]",
        border_style=COLORS["primary"]
    ))
    console.print()

    # Create info table
    table = Table(show_header=False, border_style=COLORS["gray_600"], box=None)
    table.add_column("Property", style=f"bold {COLORS['accent']}")
    table.add_column("Value", style=COLORS["white"])

    table.add_row("Name", server.name)
    table.add_row("Type", server.server_type.value)
    table.add_row("Enabled", f"{'Yes' if server.enabled else 'No'}")
    table.add_row("Read-only", f"{'Yes' if server.readonly else 'No'}")
    table.add_row("Command", server.command or "HTTP")
    table.add_row("Timeout", f"{server.timeout}s")

    if server.description:
        table.add_row("Description", server.description)

    if server.args:
        table.add_row("Arguments", ", ".join(server.args[:3]))

    if server.env:
        env_count = len(server.env)
        table.add_row("Environment", f"{env_count} variables")

    console.print(table)


def handle_mcp_enable(console: Console, manager: MCPClientManager, server_name: str) -> None:
    """Handle /mcp enable <name>."""
    if manager.enable_server(server_name):
        console.print(f"[{COLORS['success']}]{Icons.CHECK} Enabled server: {server_name}[/]")
        console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to apply changes[/]")
    else:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Server not found: {server_name}[/]")


def handle_mcp_disable(console: Console, manager: MCPClientManager, server_name: str) -> None:
    """Handle /mcp disable <name>."""
    if manager.disable_server(server_name):
        console.print(f"[{COLORS['warning']}]{Icons.INFO} Disabled server: {server_name}[/]")
        console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to apply changes[/]")
    else:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Server not found: {server_name}[/]")


def handle_mcp_remove(console: Console, manager: MCPClientManager, server_name: str) -> None:
    """Handle /mcp remove <name> - Remove server with confirmation."""
    servers = manager.list_servers()
    server = next((s for s in servers if s.name == server_name), None)

    if not server:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Server not found: {server_name}[/]")
        return

    # Confirm deletion
    console.print()
    console.print(f"[{COLORS['warning']}]{Icons.WARNING} This will remove server: {server_name}[/]")
    confirm = Confirm.ask(f"[{COLORS['gray_400']}]Are you sure?[/]", default=False)

    if not confirm:
        console.print(f"[{COLORS['info']}]{Icons.INFO} Cancelled[/]")
        return

    if manager.remove_server(server_name):
        console.print(f"[{COLORS['success']}]{Icons.CHECK} Removed server: {server_name}[/]")
    else:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Failed to remove server[/]")


def handle_mcp_reconnect(console: Console, manager: MCPClientManager, server_name: str) -> None:
    """Handle /mcp reconnect <name> - Restart a failed server."""
    console.print(f"[{COLORS['info']}]{Icons.GEAR} Reconnecting server: {server_name}...[/]")

    if manager.reconnect_server(server_name):
        console.print(f"[{COLORS['success']}]{Icons.CHECK} Server reconnected successfully[/]")
        console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to use the reconnected server[/]")
    else:
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Failed to reconnect server[/]")
        console.print(f"[{COLORS['gray_400']}]Check logs for details[/]")


def handle_mcp_add_interactive(console: Console, manager: MCPClientManager) -> None:
    """Handle /mcp add - Interactive server addition with transport type support."""
    console.print()
    console.print(Panel.fit(
        f"[bold {COLORS['primary']}]{Icons.SPARKLE} Add MCP Server[/bold {COLORS['primary']}]",
        border_style=COLORS["primary"]
    ))
    console.print()

    # Ask for server type
    console.print(f"[{COLORS['gray_400']}]Select server type:[/]")
    console.print(f"  1. [{COLORS['primary']}]MSSQL[/] - SQL Server database")
    console.print(f"  2. [{COLORS['primary']}]PostgreSQL[/] - PostgreSQL database")
    console.print(f"  3. [{COLORS['primary']}]MongoDB[/] - MongoDB database")
    console.print(f"  4. [{COLORS['primary']}]Brave Search[/] - Web search")
    console.print(f"  5. [{COLORS['primary']}]Custom[/] - Custom MCP server")
    console.print()

    choice = Prompt.ask(
        f"[{COLORS['gray_400']}]Choice[/]",
        choices=["1", "2", "3", "4", "5"],
        default="5"
    )

    server_type_map = {
        "1": MCPServerType.MSSQL,
        "2": MCPServerType.POSTGRESQL,
        "3": MCPServerType.MONGODB,
        "4": MCPServerType.BRAVE_SEARCH,
        "5": MCPServerType.CUSTOM,
    }

    server_type = server_type_map[choice]

    # Use template if available
    if server_type == MCPServerType.BRAVE_SEARCH and choice == "4":
        # Quick add Brave Search with template
        console.print()
        console.print(f"[{COLORS['info']}]{Icons.INFO} Using Brave Search template (stdio/npx)[/]")
        console.print(f"[{COLORS['gray_400']}]Set BRAVE_API_KEY environment variable before use[/]")

        try:
            manager.add_server(BRAVE_SEARCH_TEMPLATE)
            console.print(f"[{COLORS['success']}]{Icons.CHECK} Added Brave Search server[/]")
            console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to activate[/]")
        except Exception as e:
            console.print(f"[{COLORS['error']}]{Icons.CROSS} Failed: {e}[/]")
        return

    # Ask for transport type
    console.print()
    console.print(f"[{COLORS['gray_400']}]Select transport type:[/]")
    console.print(f"  1. [{COLORS['primary']}]Stdio[/] - Local subprocess (command + args)")
    console.print(f"  2. [{COLORS['primary']}]Streamable HTTP[/] - HTTP endpoint (production)")
    console.print(f"  3. [{COLORS['primary']}]SSE[/] - Server-Sent Events (legacy)")
    console.print()
    console.print(f"[{COLORS['info']}]{Icons.INFO} Most local servers use stdio, production servers use HTTP[/]")
    console.print()

    transport_choice = Prompt.ask(
        f"[{COLORS['gray_400']}]Transport[/]",
        choices=["1", "2", "3"],
        default="1"
    )

    transport_map = {
        "1": TransportType.STDIO,
        "2": TransportType.STREAMABLE_HTTP,
        "3": TransportType.SSE,
    }

    transport = transport_map[transport_choice]

    # Get server name (common for all transports)
    console.print()
    name = Prompt.ask(f"[{COLORS['gray_400']}]Server name (unique)[/]")
    if not name:
        console.print(f"[{COLORS['error']}]Name is required[/]")
        return

    # Check if name exists
    existing = manager.list_servers()
    if any(s.name == name for s in existing):
        console.print(f"[{COLORS['error']}]{Icons.CROSS} Server name already exists: {name}[/]")
        return

    # Branch based on transport type
    if transport == TransportType.STDIO:
        # Stdio transport: ask for command + args + env
        command = Prompt.ask(f"[{COLORS['gray_400']}]Command (e.g., 'node', 'python', 'npx')[/]", default="node")
        args_input = Prompt.ask(f"[{COLORS['gray_400']}]Arguments (space-separated)[/]", default="")
        args = args_input.split() if args_input else []
        
        # Optional environment variables
        console.print(f"[{COLORS['info']}]Environment variables (optional, format: KEY=value)[/]")
        console.print(f"[{COLORS['gray_400']}]Enter blank line when done[/]")
        env = {}
        while True:
            env_line = Prompt.ask(f"[{COLORS['gray_400']}]Env var[/]", default="")
            if not env_line:
                break
            if "=" in env_line:
                key, value = env_line.split("=", 1)
                env[key.strip()] = value.strip()
            else:
                console.print(f"[{COLORS['error']}]Invalid format. Use KEY=value[/]")
        
        readonly = Prompt.ask(
            f"[{COLORS['gray_400']}]Read-only mode?[/]",
            choices=["y", "n"],
            default="n"
        ) == "y"
        
        description = Prompt.ask(f"[{COLORS['gray_400']}]Description (optional)[/]", default="")
        
        # Create config
        try:
            config = MCPServerConfig(
                name=name,
                server_type=server_type,
                transport=transport,
                command=command,
                args=args,
                env=env,
                readonly=readonly,
                description=description or f"{server_type.value} server (stdio)",
            )
            
            manager.add_server(config)
            console.print()
            console.print(f"[{COLORS['success']}]{Icons.CHECK} Added stdio server: {name}[/]")
            console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to activate[/]")
            
        except Exception as e:
            console.print(f"[{COLORS['error']}]{Icons.CROSS} Failed to add server: {e}[/]")
    
    elif transport in (TransportType.STREAMABLE_HTTP, TransportType.SSE):
        # HTTP/SSE transport: ask for URL + headers
        url = Prompt.ask(f"[{COLORS['gray_400']}]Server URL (http:// or https://)[/]")
        if not url:
            console.print(f"[{COLORS['error']}]URL is required[/]")
            return
        
        # Optional HTTP headers
        console.print(f"[{COLORS['info']}]HTTP headers (optional, format: Header-Name: value)[/]")
        console.print(f"[{COLORS['gray_400']}]Enter blank line when done[/]")
        headers = {}
        while True:
            header_line = Prompt.ask(f"[{COLORS['gray_400']}]Header[/]", default="")
            if not header_line:
                break
            if ":" in header_line:
                key, value = header_line.split(":", 1)
                headers[key.strip()] = value.strip()
            else:
                console.print(f"[{COLORS['error']}]Invalid format. Use Header-Name: value[/]")
        
        readonly = Prompt.ask(
            f"[{COLORS['gray_400']}]Read-only mode?[/]",
            choices=["y", "n"],
            default="n"
        ) == "y"
        
        description = Prompt.ask(f"[{COLORS['gray_400']}]Description (optional)[/]", default="")
        
        # Create config
        try:
            config = MCPServerConfig(
                name=name,
                server_type=server_type,
                transport=transport,
                url=url,
                headers=headers,
                readonly=readonly,
                description=description or f"{server_type.value} server ({transport.value})",
            )
            
            manager.add_server(config)
            console.print()
            console.print(f"[{COLORS['success']}]{Icons.CHECK} Added {transport.value} server: {name}[/]")
            console.print(f"[{COLORS['gray_400']}]{Icons.INFO} Restart chat to activate[/]")
            
        except Exception as e:
            console.print(f"[{COLORS['error']}]{Icons.CROSS} Failed to add server: {e}[/]")


def handle_mcp_tools(console: Console, manager: MCPClientManager, server_name: str | None = None) -> None:
    """Handle /mcp tools [name] - List available tools."""
    console.print()
    console.print(f"[{COLORS['info']}]{Icons.INFO} Tool listing requires server restart[/]")
    console.print(f"[{COLORS['gray_400']}]This feature will be available after implementing agent hot-reload[/]")


def handle_mcp_command(console: Console, command: str) -> bool:
    """
    Handle /mcp commands.

    Returns:
        True if command was handled, False otherwise
    """
    parts = command.split()

    if len(parts) == 1:
        # Just "/mcp" - show list
        manager = MCPClientManager()
        handle_mcp_list(console, manager)
        return True

    subcommand = parts[1].lower()
    manager = MCPClientManager()

    if subcommand == "list":
        handle_mcp_list(console, manager)

    elif subcommand == "status":
        if len(parts) < 3:
            console.print(f"[{COLORS['error']}]Usage: /mcp status <server-name>[/]")
        else:
            handle_mcp_status(console, manager, parts[2])

    elif subcommand == "enable":
        if len(parts) < 3:
            console.print(f"[{COLORS['error']}]Usage: /mcp enable <server-name>[/]")
        else:
            handle_mcp_enable(console, manager, parts[2])

    elif subcommand == "disable":
        if len(parts) < 3:
            console.print(f"[{COLORS['error']}]Usage: /mcp disable <server-name>[/]")
        else:
            handle_mcp_disable(console, manager, parts[2])

    elif subcommand == "remove":
        if len(parts) < 3:
            console.print(f"[{COLORS['error']}]Usage: /mcp remove <server-name>[/]")
        else:
            handle_mcp_remove(console, manager, parts[2])

    elif subcommand == "reconnect":
        if len(parts) < 3:
            console.print(f"[{COLORS['error']}]Usage: /mcp reconnect <server-name>[/]")
        else:
            handle_mcp_reconnect(console, manager, parts[2])

    elif subcommand == "add":
        handle_mcp_add_interactive(console, manager)

    elif subcommand == "tools":
        server_name = parts[2] if len(parts) >= 3 else None
        handle_mcp_tools(console, manager, server_name)

    else:
        console.print(f"[{COLORS['error']}]Unknown subcommand: {subcommand}[/]")
        console.print()
        console.print(f"[{COLORS['gray_400']}]Available subcommands:[/]")
        console.print(f"  • [{COLORS['primary']}]list[/] - List all MCP servers")
        console.print(f"  • [{COLORS['primary']}]status <name>[/] - Show server details")
        console.print(f"  • [{COLORS['primary']}]add[/] - Add new server interactively")
        console.print(f"  • [{COLORS['primary']}]remove <name>[/] - Remove server")
        console.print(f"  • [{COLORS['primary']}]enable <name>[/] - Enable server")
        console.print(f"  • [{COLORS['primary']}]disable <name>[/] - Disable server")
        console.print(f"  • [{COLORS['primary']}]reconnect <name>[/] - Restart failed server")
        console.print(f"  • [{COLORS['primary']}]tools [name][/] - List available tools")

    return True
