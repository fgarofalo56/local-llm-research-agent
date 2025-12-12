"""
Local LLM Research Analytics Tool

Main entry point for the application. Provides commands to start the CLI chat
or Streamlit web UI.

Usage:
    python -m src.main cli      # Start CLI chat
    python -m src.main ui       # Start Streamlit UI
    python -m src.main --help   # Show help
"""

import typer
from rich.console import Console

app = typer.Typer(
    name="llm-research", help="Local LLM Research Analytics Tool - Chat with your SQL Server data"
)
console = Console()


@app.command()
def cli():
    """Start the CLI chat interface."""
    try:
        from src.cli.chat import main as chat_main

        chat_main()
    except ImportError as e:
        console.print(f"[red]Error loading CLI module: {e}[/]")
        console.print("[yellow]Make sure you've installed all dependencies: uv sync[/]")
        raise typer.Exit(1)


@app.command()
def ui():
    """Start the Streamlit web UI."""
    import subprocess
    import sys

    console.print("[green]Starting Streamlit UI...[/]")
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "src/ui/streamlit_app.py"], check=True
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting Streamlit: {e}[/]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Streamlit stopped.[/]")


@app.command()
def check():
    """Check system requirements and configuration."""
    from pathlib import Path

    import httpx

    console.print("\n[bold]System Check[/bold]\n")

    # Check Ollama
    console.print("Checking Ollama...", end=" ")
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            console.print("[green]OK - Running[/]")
            models = response.json().get("models", [])
            if models:
                console.print(f"  Available models: {', '.join(m['name'] for m in models[:5])}")
        else:
            console.print("[yellow]Warning - Running but unexpected response[/]")
    except Exception:
        console.print("[red]ERROR - Not running[/]")
        console.print("  Install Ollama from https://ollama.com/")

    # Check .env file
    console.print("Checking .env file...", end=" ")
    if Path(".env").exists():
        console.print("[green]OK - Found[/]")
    else:
        console.print("[yellow]Warning - Not found[/]")
        console.print("  Copy .env.example to .env and configure")

    # Check MCP config
    console.print("Checking mcp_config.json...", end=" ")
    if Path("mcp_config.json").exists():
        console.print("[green]OK - Found[/]")
    else:
        console.print("[yellow]Warning - Not found[/]")

    console.print()


@app.callback()
def main():
    """Local LLM Research Analytics Tool"""
    pass


if __name__ == "__main__":
    app()
