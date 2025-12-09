"""
CLI Chat Interface

Interactive command-line chat interface using Typer and Rich.
Provides a terminal-based way to interact with the research agent.
"""

import asyncio

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.agent.research_agent import ResearchAgent, ResearchAgentError
from src.utils.config import settings
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

app = typer.Typer(
    name="llm-chat",
    help="Local LLM Research Agent - Chat with your SQL Server data",
    no_args_is_help=False,
)
console = Console()


def check_ollama_connection() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_model_available(model_name: str) -> bool:
    """Check if the specified model is available in Ollama."""
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model_name in m.get("name", "") for m in models)
    except Exception:
        pass
    return False


def print_welcome() -> None:
    """Print welcome message and status."""
    console.print()
    console.print(
        Panel.fit(
            "[bold green]Local LLM Research Agent[/]\n\n"
            "Chat with your SQL Server data using natural language.\n"
            "Type [bold]'quit'[/] to exit, [bold]'clear'[/] to reset conversation.",
            title="Welcome",
            border_style="green",
        )
    )
    console.print()


def print_status() -> None:
    """Print connection status."""
    table = Table(show_header=False, box=None)
    table.add_column("Item", style="cyan")
    table.add_column("Status")

    # Ollama status
    ollama_ok = check_ollama_connection()
    ollama_status = "[green]Connected[/]" if ollama_ok else "[red]Not Running[/]"
    table.add_row("Ollama", ollama_status)

    # Model status
    if ollama_ok:
        model_ok = check_model_available(settings.ollama_model)
        model_status = "[green]Available[/]" if model_ok else "[yellow]Not Found[/]"
    else:
        model_status = "[dim]Unknown[/]"
    table.add_row(f"Model ({settings.ollama_model})", model_status)

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
    console.print("  [cyan]help[/]                - Show this help message")
    console.print()


async def run_chat_loop(readonly: bool = False) -> None:
    """
    Run the interactive chat loop.

    Args:
        readonly: Enable read-only mode for safety
    """
    # Check prerequisites
    if not check_ollama_connection():
        console.print(
            "[red]Error:[/] Ollama is not running.\n"
            "Please start Ollama: [cyan]ollama serve[/]"
        )
        raise typer.Exit(1)

    if not settings.mcp_mssql_path:
        console.print(
            "[yellow]Warning:[/] MCP_MSSQL_PATH is not set.\n"
            "SQL Server tools will not be available.\n"
            "Set this in your .env file."
        )

    try:
        agent = ResearchAgent(readonly=readonly)
    except Exception as e:
        console.print(f"[red]Error creating agent:[/] {e}")
        raise typer.Exit(1)

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
                print_status()
                continue

            if command == "help":
                print_help_commands()
                continue

            # Send to agent
            with console.status("[bold green]Thinking...[/]", spinner="dots"):
                response = await agent.chat(user_input)

            # Display response
            console.print()
            console.print(f"[bold green]Agent:[/] {response}")

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
    readonly: bool = typer.Option(
        False,
        "--readonly",
        "-r",
        help="Enable read-only mode (no data modifications)",
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

    print_welcome()
    print_status()

    try:
        asyncio.run(run_chat_loop(readonly=readonly))
    except Exception as e:
        console.print(f"[red]Fatal error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show current configuration and connection status."""
    console.print("\n[bold]Configuration Status[/]\n")
    print_status()


@app.command()
def query(
    message: str = typer.Argument(..., help="Query to send to the agent"),
    readonly: bool = typer.Option(True, "--readonly", "-r", help="Read-only mode"),
) -> None:
    """Send a single query to the agent and exit."""

    async def run_query() -> None:
        if not check_ollama_connection():
            console.print("[red]Error:[/] Ollama is not running.")
            raise typer.Exit(1)

        try:
            agent = ResearchAgent(readonly=readonly)
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
