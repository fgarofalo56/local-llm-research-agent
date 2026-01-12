"""
CLI Command Handlers

Extracted command handlers for the chat loop to improve maintainability.
Each handler returns a tuple of (handled: bool, should_continue: bool).
"""

from rich.console import Console
from rich.prompt import Prompt

from src.cli.theme import (
    COLORS,
    create_session_table,
    error_message,
    success_message,
    warning_message,
)
from src.utils.export import (
    export_conversation_to_csv,
    export_to_json,
    export_to_markdown,
    generate_export_filename,
)
from src.utils.history import get_history_manager


async def handle_clear_command(agent, console: Console) -> tuple[bool, bool]:
    """Handle the 'clear' command to clear conversation history."""
    agent.clear_history()
    console.print(success_message("Conversation cleared"))
    return True, True  # handled, continue


async def handle_cache_command(agent, console: Console) -> tuple[bool, bool]:
    """Handle the 'cache' command to show cache statistics."""
    from src.cli.chat import print_cache_stats

    print_cache_stats(agent)
    return True, True


async def handle_cache_clear_command(agent, console: Console) -> tuple[bool, bool]:
    """Handle the 'cache-clear' command to clear the cache."""
    count = agent.clear_cache()
    console.print(success_message(f"Cache cleared ({count} entries removed)"))
    return True, True


async def handle_export_command(
    command: str, agent, console: Console
) -> tuple[bool, bool]:
    """Handle the 'export' command to export conversation."""
    parts = command.split()
    if len(parts) == 1:
        # Prompt for format
        fmt = Prompt.ask(
            f"[{COLORS['gray_400']}]Export format[/]",
            choices=["json", "csv", "md"],
            default="json",
        )
    else:
        fmt = parts[1].lower()

    if agent.conversation.total_turns == 0:
        console.print(warning_message("No conversation to export"))
        return True, True

    try:
        filename = generate_export_filename("chat", fmt)
        if fmt == "json":
            export_to_json(agent.conversation, filename)
        elif fmt == "csv":
            export_conversation_to_csv(agent.conversation, filename)
        elif fmt in ("md", "markdown"):
            export_to_markdown(agent.conversation, filename)
        else:
            console.print(error_message(f"Unknown format: {fmt}"))
            return True, True
        console.print(success_message(f"Exported to: {filename}"))
    except Exception as e:
        console.print(error_message(f"Export failed: {e}"))
    return True, True


async def handle_history_command(
    command: str, agent, console: Console, provider: str, model: str
) -> tuple[bool, bool]:
    """Handle the 'history' command for session management."""
    parts = command.split()
    history = get_history_manager()

    if len(parts) == 1:
        # List sessions
        sessions = history.list_sessions(limit=10)
        if not sessions:
            console.print(warning_message("No saved sessions"))
        else:
            console.print()
            table = create_session_table()
            for session in sessions:
                table.add_row(
                    session.session_id,
                    session.title[:35],
                    str(session.turn_count),
                    session.updated_at.strftime("%Y-%m-%d %H:%M"),
                )
            console.print(table)
        return True, True

    elif parts[1] == "save":
        if agent.conversation.total_turns == 0:
            console.print(warning_message("No conversation to save"))
        else:
            title = Prompt.ask(f"[{COLORS['gray_400']}]Session title[/]", default="")
            session_id = history.save_session(
                agent.conversation,
                title=title if title else None,
                provider=provider,
                model=model or "",
            )
            console.print(success_message(f"Session saved: {session_id}"))
        return True, True

    elif parts[1] == "load" and len(parts) >= 3:
        session_id = parts[2]
        session = history.load_session(session_id)
        if session:
            # Restore conversation
            agent.conversation = session.to_conversation()
            console.print(success_message(f"Session loaded: {session.title}"))
        else:
            console.print(error_message(f"Session not found: {session_id}"))
        return True, True

    elif parts[1] == "delete" and len(parts) >= 3:
        session_id = parts[2]
        if history.delete_session(session_id):
            console.print(success_message(f"Session deleted: {session_id}"))
        else:
            console.print(error_message(f"Session not found: {session_id}"))
        return True, True

    return False, True  # Not handled


async def handle_help_command(console: Console) -> tuple[bool, bool]:
    """Handle the 'help' command to show help panel."""
    from src.cli.theme import create_help_panel

    console.print()
    console.print(create_help_panel())
    return True, True


__all__ = [
    "handle_clear_command",
    "handle_cache_command",
    "handle_cache_clear_command",
    "handle_export_command",
    "handle_history_command",
    "handle_help_command",
]
