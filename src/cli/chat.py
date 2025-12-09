"""
CLI Chat Interface

Interactive command-line chat interface using Typer and Rich.
Provides a terminal-based way to interact with the research agent.
Supports both Ollama and Foundry Local as LLM providers.
"""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.agent.research_agent import ResearchAgent, ResearchAgentError
from src.providers import ProviderType, create_provider, get_available_providers
from src.utils.config import settings
from src.utils.database_manager import DatabaseConfig, get_database_manager
from src.utils.export import (
    export_conversation_to_csv,
    export_response_data,
    export_to_json,
    export_to_markdown,
    generate_export_filename,
)
from src.utils.health import (
    HealthStatus,
    format_health_report,
    run_health_checks,
)
from src.utils.history import get_history_manager
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

app = typer.Typer(
    name="llm-chat",
    help="Local LLM Research Agent - Chat with your SQL Server data",
    no_args_is_help=False,
)
console = Console()


async def check_provider_status(provider_type: str | None = None) -> dict:
    """
    Check provider connection status.

    Args:
        provider_type: Specific provider to check, or None for configured provider

    Returns:
        Dict with provider status information
    """
    try:
        ptype = ProviderType(provider_type) if provider_type else ProviderType(settings.llm_provider)
        provider = create_provider(provider_type=ptype)
        status = await provider.check_connection()
        return {
            "available": status.available,
            "provider": status.provider_type.value,
            "model": status.model_name,
            "endpoint": status.endpoint,
            "error": status.error,
            "version": status.version,
        }
    except Exception as e:
        return {
            "available": False,
            "provider": provider_type or settings.llm_provider,
            "error": str(e),
        }


def print_welcome(provider_type: str) -> None:
    """Print welcome message and status."""
    console.print()
    provider_name = "Ollama" if provider_type == "ollama" else "Foundry Local"
    console.print(
        Panel.fit(
            f"[bold green]Local LLM Research Agent[/]\n\n"
            f"Chat with your SQL Server data using natural language.\n"
            f"Provider: [cyan]{provider_name}[/]\n"
            "Type [bold]'quit'[/] to exit, [bold]'clear'[/] to reset conversation.",
            title="Welcome",
            border_style="green",
        )
    )
    console.print()


def print_status_sync(provider_type: str | None = None) -> None:
    """Print connection status (synchronous wrapper)."""
    asyncio.run(print_status_async(provider_type))


async def print_status_async(provider_type: str | None = None) -> None:
    """Print connection status."""
    table = Table(show_header=False, box=None)
    table.add_column("Item", style="cyan")
    table.add_column("Status")

    # Get all provider statuses
    statuses = await get_available_providers()

    for status in statuses:
        provider_name = "Ollama" if status.provider_type == ProviderType.OLLAMA else "Foundry Local"
        if status.available:
            status_text = f"[green]Connected[/] ({status.model_name})"
            if status.version:
                status_text += f" v{status.version}"
        else:
            status_text = f"[red]Not Available[/]"
            if status.error:
                status_text += f" - {status.error[:50]}"

        # Highlight active provider
        active = (provider_type or settings.llm_provider) == status.provider_type.value
        if active:
            provider_name = f"[bold]{provider_name}[/] (active)"

        table.add_row(provider_name, status_text)

    # MCP config status
    mcp_path = settings.mcp_mssql_path
    mcp_status = "[green]Configured[/]" if mcp_path else "[yellow]Not Set[/]"
    table.add_row("MCP MSSQL Path", mcp_status)

    # Read-only mode
    readonly_status = "[cyan]Yes[/]" if settings.mcp_mssql_readonly else "[yellow]No[/]"
    table.add_row("Read-Only Mode", readonly_status)

    console.print(table)
    console.print()


def print_help_commands() -> None:
    """Print available commands."""
    console.print("[bold]Commands:[/]")
    console.print("  [cyan]quit[/], [cyan]exit[/], [cyan]q[/]  - Exit the chat")
    console.print("  [cyan]clear[/]               - Clear conversation history")
    console.print("  [cyan]status[/]              - Show connection status")
    console.print("  [cyan]cache[/]               - Show cache statistics")
    console.print("  [cyan]cache-clear[/]         - Clear the response cache")
    console.print("  [cyan]export[/]              - Export conversation (prompts for format)")
    console.print("  [cyan]export json[/]         - Export conversation to JSON")
    console.print("  [cyan]export csv[/]          - Export conversation to CSV")
    console.print("  [cyan]export md[/]           - Export conversation to Markdown")
    console.print("  [cyan]history[/]             - List saved sessions")
    console.print("  [cyan]history load <id>[/]   - Load a saved session")
    console.print("  [cyan]history save[/]        - Save current session")
    console.print("  [cyan]history delete <id>[/] - Delete a saved session")
    console.print("  [cyan]db[/]                  - List configured databases")
    console.print("  [cyan]db switch <name>[/]    - Switch to a different database")
    console.print("  [cyan]db add[/]              - Add a new database configuration")
    console.print("  [cyan]db remove <name>[/]    - Remove a database configuration")
    console.print("  [cyan]help[/]                - Show this help message")
    console.print()


def print_cache_stats(agent: ResearchAgent) -> None:
    """Print cache statistics."""
    stats = agent.get_cache_stats()
    table = Table(show_header=False, box=None)
    table.add_column("Item", style="cyan")
    table.add_column("Value")

    table.add_row("Cache Enabled", "[green]Yes[/]" if agent.cache_enabled else "[red]No[/]")
    table.add_row("Entries", str(stats.size))
    table.add_row("Max Size", str(stats.max_size))
    table.add_row("TTL", f"{stats.ttl_seconds}s" if stats.ttl_seconds > 0 else "No expiration")
    table.add_row("Hits", str(stats.hits))
    table.add_row("Misses", str(stats.misses))
    table.add_row("Hit Rate", stats.to_dict()["hit_rate"])
    table.add_row("Evictions", str(stats.evictions))

    console.print(table)
    console.print()


async def run_chat_loop(
    provider_type: str | None = None,
    model: str | None = None,
    readonly: bool = False,
    stream: bool = False,
    cache_enabled: bool = True,
    explain_mode: bool = False,
) -> None:
    """
    Run the interactive chat loop.

    Args:
        provider_type: LLM provider ('ollama' or 'foundry_local')
        model: Model name to use
        readonly: Enable read-only mode for safety
        stream: Enable streaming responses
        cache_enabled: Enable response caching
        explain_mode: Enable educational SQL query explanations
    """
    # Use configured provider if not specified
    effective_provider = provider_type or settings.llm_provider

    # Check provider connection
    status = await check_provider_status(effective_provider)
    if not status["available"]:
        error_msg = status.get("error", "Unknown error")
        if effective_provider == "ollama":
            console.print(
                f"[red]Error:[/] Ollama is not available.\n"
                f"Reason: {error_msg}\n"
                "Please start Ollama: [cyan]ollama serve[/]"
            )
        else:
            console.print(
                f"[red]Error:[/] Foundry Local is not available.\n"
                f"Reason: {error_msg}\n"
                "Start with: [cyan]pip install foundry-local-sdk[/] and use FoundryLocalManager"
            )
        raise typer.Exit(1)

    if not settings.mcp_mssql_path:
        console.print(
            "[yellow]Warning:[/] MCP_MSSQL_PATH is not set.\n"
            "SQL Server tools will not be available.\n"
            "Set this in your .env file."
        )

    try:
        agent = ResearchAgent(
            provider_type=effective_provider,
            model_name=model,
            readonly=readonly,
            cache_enabled=cache_enabled,
            explain_mode=explain_mode,
        )
    except Exception as e:
        console.print(f"[red]Error creating agent:[/] {e}")
        raise typer.Exit(1)

    # Show mode status
    mode_info = []
    if cache_enabled:
        mode_info.append(f"cache (max {settings.cache_max_size})")
    if explain_mode:
        mode_info.append("[cyan]explain mode[/]")
    if mode_info:
        console.print(f"[dim]Features: {', '.join(mode_info)}[/]")
    console.print()

    print_help_commands()

    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold blue]You[/]")

            if not user_input.strip():
                continue

            # Handle commands
            command = user_input.strip().lower()

            if command in ("quit", "exit", "q"):
                console.print("[yellow]Goodbye![/]")
                break

            if command == "clear":
                agent.clear_history()
                console.print("[yellow]Conversation cleared.[/]")
                continue

            if command == "status":
                await print_status_async(effective_provider)
                continue

            if command == "cache":
                print_cache_stats(agent)
                continue

            if command == "cache-clear":
                count = agent.clear_cache()
                console.print(f"[yellow]Cache cleared ({count} entries removed).[/]")
                continue

            if command.startswith("export"):
                parts = command.split()
                if len(parts) == 1:
                    # Prompt for format
                    fmt = Prompt.ask(
                        "Export format",
                        choices=["json", "csv", "md"],
                        default="json",
                    )
                else:
                    fmt = parts[1].lower()

                if agent.conversation.total_turns == 0:
                    console.print("[yellow]No conversation to export.[/]")
                    continue

                try:
                    filename = generate_export_filename("chat", fmt)
                    if fmt == "json":
                        export_to_json(agent.conversation, filename)
                    elif fmt == "csv":
                        export_conversation_to_csv(agent.conversation, filename)
                    elif fmt in ("md", "markdown"):
                        export_to_markdown(agent.conversation, filename)
                    else:
                        console.print(f"[red]Unknown format: {fmt}[/]")
                        continue
                    console.print(f"[green]Exported to:[/] {filename}")
                except Exception as e:
                    console.print(f"[red]Export failed:[/] {e}")
                continue

            if command.startswith("history"):
                parts = command.split()
                history = get_history_manager()

                if len(parts) == 1:
                    # List sessions
                    sessions = history.list_sessions(limit=10)
                    if not sessions:
                        console.print("[yellow]No saved sessions.[/]")
                    else:
                        console.print("\n[bold]Saved Sessions:[/]")
                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("ID", width=10)
                        table.add_column("Title", width=40)
                        table.add_column("Turns", justify="right")
                        table.add_column("Updated", width=16)

                        for session in sessions:
                            table.add_row(
                                session.session_id,
                                session.title[:40],
                                str(session.turn_count),
                                session.updated_at.strftime("%Y-%m-%d %H:%M"),
                            )
                        console.print(table)
                    continue

                elif parts[1] == "save":
                    if agent.conversation.total_turns == 0:
                        console.print("[yellow]No conversation to save.[/]")
                    else:
                        title = Prompt.ask("Session title", default="")
                        session_id = history.save_session(
                            agent.conversation,
                            title=title if title else None,
                            provider=effective_provider,
                            model=model or "",
                        )
                        console.print(f"[green]Session saved:[/] {session_id}")
                    continue

                elif parts[1] == "load" and len(parts) >= 3:
                    session_id = parts[2]
                    session = history.load_session(session_id)
                    if session:
                        # Restore conversation
                        agent.conversation = session.to_conversation()
                        console.print(f"[green]Session loaded:[/] {session.metadata.title}")
                        console.print(f"  {session.metadata.turn_count} turns restored")
                    else:
                        console.print(f"[red]Session not found:[/] {session_id}")
                    continue

                elif parts[1] == "delete" and len(parts) >= 3:
                    session_id = parts[2]
                    if history.delete_session(session_id):
                        console.print(f"[green]Session deleted:[/] {session_id}")
                    else:
                        console.print(f"[red]Session not found:[/] {session_id}")
                    continue

                else:
                    console.print("[yellow]Usage: history [list|save|load <id>|delete <id>][/]")
                    continue

            if command.startswith("db"):
                parts = command.split()
                db_manager = get_database_manager()

                if len(parts) == 1:
                    # List databases
                    databases = db_manager.list_databases()
                    console.print("\n[bold]Configured Databases:[/]")
                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("Name", width=15)
                    table.add_column("Host", width=20)
                    table.add_column("Database", width=20)
                    table.add_column("Mode", width=10)
                    table.add_column("Active", width=8)

                    for db in databases:
                        mode = "[cyan]RO[/]" if db["readonly"] else "RW"
                        active = "[green]Yes[/]" if db["active"] else ""
                        table.add_row(
                            db["name"],
                            db["host"],
                            db["database"],
                            mode,
                            active,
                        )
                    console.print(table)
                    continue

                elif parts[1] == "switch" and len(parts) >= 3:
                    db_name = parts[2]
                    if db_manager.set_active(db_name):
                        db_config = db_manager.active
                        console.print(f"[green]Switched to database:[/] {db_name}")
                        console.print(f"  Connection: {db_config.connection_string_display}")
                        # Note: Agent would need to be recreated to use new database
                        console.print("[yellow]Note: Restart chat to apply new database connection.[/]")
                    else:
                        console.print(f"[red]Database not found:[/] {db_name}")
                    continue

                elif parts[1] == "add":
                    console.print("\n[bold]Add New Database Configuration[/]")
                    name = Prompt.ask("Database name (unique identifier)")
                    if not name:
                        console.print("[red]Name is required.[/]")
                        continue

                    host = Prompt.ask("SQL Server host", default="localhost")
                    port = int(Prompt.ask("Port", default="1433"))
                    database = Prompt.ask("Database name")
                    username = Prompt.ask("Username (blank for Windows Auth)", default="")
                    password = ""
                    if username:
                        password = Prompt.ask("Password", password=True, default="")
                    readonly = Prompt.ask("Read-only mode?", choices=["y", "n"], default="n") == "y"
                    description = Prompt.ask("Description (optional)", default="")

                    try:
                        config = DatabaseConfig(
                            name=name,
                            host=host,
                            port=port,
                            database=database,
                            username=username,
                            password=password,
                            readonly=readonly,
                            description=description,
                        )
                        db_manager.add_database(config)
                        console.print(f"[green]Database added:[/] {name}")
                    except Exception as e:
                        console.print(f"[red]Failed to add database:[/] {e}")
                    continue

                elif parts[1] == "remove" and len(parts) >= 3:
                    db_name = parts[2]
                    if db_manager.remove_database(db_name):
                        console.print(f"[green]Database removed:[/] {db_name}")
                    else:
                        console.print(f"[red]Cannot remove database:[/] {db_name}")
                        console.print("  (default database cannot be removed)")
                    continue

                else:
                    console.print("[yellow]Usage: db [list|switch <name>|add|remove <name>][/]")
                    continue

            if command == "help":
                print_help_commands()
                continue

            # Send to agent
            console.print()
            console.print("[bold green]Agent:[/] ", end="")

            if stream:
                # Streaming mode - print chunks as they arrive
                async for chunk in agent.chat_stream(user_input):
                    console.print(chunk, end="")
                console.print()  # Final newline
            else:
                # Non-streaming mode - show spinner while waiting
                with console.status("[bold green]Thinking...[/]", spinner="dots"):
                    response = await agent.chat(user_input)
                console.print(response)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/]")
            continue

        except ResearchAgentError as e:
            console.print(f"\n[red]Agent error:[/] {e}")
            continue

        except Exception as e:
            logger.exception("chat_loop_error")
            console.print(f"\n[red]Unexpected error:[/] {e}")
            continue


@app.command()
def chat(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider: 'ollama' or 'foundry_local' (default from settings)",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name/alias to use (default from settings)",
    ),
    readonly: bool = typer.Option(
        False,
        "--readonly",
        "-r",
        help="Enable read-only mode (no data modifications)",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        "-s",
        help="Enable streaming responses (show tokens as generated)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable response caching",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="Enable SQL explanation mode (educational, explains queries step by step)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
) -> None:
    """Start an interactive chat session with the research agent."""
    if debug:
        setup_logging("DEBUG")

    effective_provider = provider or settings.llm_provider
    print_welcome(effective_provider)
    print_status_sync(effective_provider)

    try:
        asyncio.run(run_chat_loop(
            provider_type=provider,
            model=model,
            readonly=readonly,
            stream=stream,
            cache_enabled=not no_cache,
            explain_mode=explain,
        ))
    except Exception as e:
        console.print(f"[red]Fatal error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def health(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed component information",
    ),
    database: bool = typer.Option(
        False,
        "--database",
        "-d",
        help="Include database connectivity check (slower)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON",
    ),
) -> None:
    """Run system health checks on LLM providers, MCP server, and database."""
    import json

    async def run_checks() -> None:
        with console.status("[bold blue]Running health checks..."):
            result = await run_health_checks(include_database=database)

        if json_output:
            console.print(json.dumps(result.to_dict(), indent=2))
        else:
            # Color-coded output
            status_colors = {
                HealthStatus.HEALTHY: "green",
                HealthStatus.UNHEALTHY: "red",
                HealthStatus.DEGRADED: "yellow",
                HealthStatus.UNKNOWN: "dim",
            }
            status_icons = {
                HealthStatus.HEALTHY: "[OK]",
                HealthStatus.UNHEALTHY: "[FAIL]",
                HealthStatus.DEGRADED: "[WARN]",
                HealthStatus.UNKNOWN: "[?]",
            }

            color = status_colors.get(result.status, "white")
            console.print(f"\n[bold]System Health:[/] [{color}]{result.status.value.upper()}[/]\n")

            # Create table for components
            table = Table(show_header=True, header_style="bold")
            table.add_column("Component", style="cyan")
            table.add_column("Status")
            table.add_column("Message")
            if verbose:
                table.add_column("Latency")

            for component in result.components:
                comp_color = status_colors.get(component.status, "white")
                icon = status_icons.get(component.status, "[?]")
                status_str = f"[{comp_color}]{icon} {component.status.value}[/]"

                if verbose and component.latency_ms:
                    latency = f"{component.latency_ms:.0f}ms"
                    table.add_row(component.name, status_str, component.message, latency)
                else:
                    table.add_row(component.name, status_str, component.message)

            console.print(table)

            if verbose:
                console.print("\n[bold]Details:[/]")
                for component in result.components:
                    if component.details:
                        console.print(f"\n  [cyan]{component.name}:[/]")
                        for key, value in component.details.items():
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value[:5])
                            console.print(f"    {key}: {value}")

            console.print()

    try:
        asyncio.run(run_checks())
    except Exception as e:
        console.print(f"[red]Health check failed:[/] {e}")
        raise typer.Exit(1)


@app.command()
def status(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Check specific provider status",
    ),
) -> None:
    """Show current configuration and connection status."""
    console.print("\n[bold]Configuration Status[/]\n")
    print_status_sync(provider)


@app.command()
def query(
    message: str = typer.Argument(..., help="Query to send to the agent"),
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to use",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name to use",
    ),
    readonly: bool = typer.Option(True, "--readonly", "-r", help="Read-only mode"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable response caching"),
) -> None:
    """Send a single query to the agent and exit."""

    async def run_query() -> None:
        effective_provider = provider or settings.llm_provider
        status = await check_provider_status(effective_provider)

        if not status["available"]:
            console.print(f"[red]Error:[/] {effective_provider} is not available.")
            if status.get("error"):
                console.print(f"Reason: {status['error']}")
            raise typer.Exit(1)

        try:
            agent = ResearchAgent(
                provider_type=provider,
                model_name=model,
                readonly=readonly,
                cache_enabled=not no_cache,
            )
            if stream:
                async for chunk in agent.chat_stream(message):
                    console.print(chunk, end="")
                console.print()
            else:
                with console.status("[bold green]Processing...[/]", spinner="dots"):
                    response = await agent.chat(message)
                console.print(response)
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)

    asyncio.run(run_query())


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
