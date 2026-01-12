"""
CLI Chat Interface

Interactive command-line chat interface using Typer and Rich.
Provides a terminal-based way to interact with the research agent.
Supports both Ollama and Foundry Local as LLM providers.
"""

import asyncio
import sys

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from rich.prompt import Prompt
from rich.text import Text

from src.agent.research_agent import ResearchAgent, ResearchAgentError
from src.cli.theme import (
    COLORS,
    Icons,
    create_console,
    create_database_table,
    create_help_panel,
    create_session_table,
    create_status_table,
    create_welcome_panel,
    error_message,
    format_agent_response_header,
    format_goodbye,
    format_token_usage,
    info_message,
    print_banner,
    styled_divider,
    success_message,
    thinking_status,
    warning_message,
)
from src.providers import ProviderType, create_provider, get_available_providers
from src.utils.config import SqlAuthType, settings
from src.utils.database_manager import DatabaseConfig, get_database_manager
from src.utils.export import (
    export_conversation_to_csv,
    export_to_json,
    export_to_markdown,
    generate_export_filename,
)
from src.utils.health import (
    HealthStatus,
    run_health_checks,
)
from src.utils.history import get_history_manager
from src.utils.logger import get_logger, setup_logging
from src.cli.command_handlers import (
    handle_clear_command,
    handle_cache_command,
    handle_cache_clear_command,
    handle_export_command,
    handle_help_command,
)

logger = get_logger(__name__)

app = typer.Typer(
    name="agent-ai",
    help="Agent AI - SQL Server Analytics with Local LLMs",
    no_args_is_help=False,
)
console = create_console()


async def check_provider_status(provider_type: str | None = None) -> dict:
    """
    Check provider connection status.

    Args:
        provider_type: Specific provider to check, or None for configured provider

    Returns:
        Dict with provider status information
    """
    try:
        ptype = (
            ProviderType(provider_type) if provider_type else ProviderType(settings.llm_provider)
        )
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


def print_welcome(provider_type: str, model: str = "", readonly: bool = False) -> None:
    """Print welcome banner and status."""
    # Print the ASCII art banner using theme function
    print_banner(console)
    # Print the welcome panel with provider info
    console.print(create_welcome_panel(provider_type, model, readonly))
    console.print()


def print_status_sync(provider_type: str | None = None) -> None:
    """Print connection status (synchronous wrapper)."""
    asyncio.run(print_status_async(provider_type))


async def print_status_async(provider_type: str | None = None) -> None:
    """Print connection status with styled table."""
    table = create_status_table(show_header=True)
    table.add_column(f"{Icons.LIGHTNING} Component", style=COLORS["accent"])
    table.add_column("Status")
    table.add_column("Details", style=COLORS["gray_400"])

    # Get all provider statuses
    statuses = await get_available_providers()

    for status in statuses:
        provider_name = "Ollama" if status.provider_type == ProviderType.OLLAMA else "Foundry Local"

        if status.available:
            status_text = Text()
            status_text.append(f"{Icons.CHECK} ", style=COLORS["success"])
            status_text.append("Connected", style=COLORS["success"])
            details = status.model_name or ""
            if status.version:
                details += f" (v{status.version})"
        else:
            status_text = Text()
            status_text.append(f"{Icons.CROSS} ", style=COLORS["error"])
            status_text.append("Not Available", style=COLORS["error"])
            details = status.error[:50] if status.error else ""

        # Highlight active provider
        active = (provider_type or settings.llm_provider) == status.provider_type.value
        if active:
            name_text = Text()
            name_text.append(f"{Icons.STAR} ", style=COLORS["accent"])
            name_text.append(provider_name, style=f"bold {COLORS['accent']}")
            name_text.append(" (active)", style=COLORS["gray_400"])
        else:
            name_text = Text(provider_name)

        table.add_row(name_text, status_text, details)

    # MCP config status
    mcp_path = settings.mcp_mssql_path
    mcp_status = Text()
    if mcp_path:
        mcp_status.append(f"{Icons.CHECK} ", style=COLORS["success"])
        mcp_status.append("Configured", style=COLORS["success"])
    else:
        mcp_status.append(f"{Icons.WARNING} ", style=COLORS["warning"])
        mcp_status.append("Not Set", style=COLORS["warning"])
    table.add_row(f"{Icons.DATABASE} MCP MSSQL", mcp_status, "")

    # SQL Server connection info
    sql_server = settings.sql_server_host
    sql_db = settings.sql_database_name
    sql_info = f"{sql_server}/{sql_db}"
    if settings.is_azure_sql:
        sql_info += " (Azure)"
    table.add_row(f"{Icons.DATABASE} SQL Server", sql_info, "")

    # Authentication type
    auth_status = Text()
    auth_type = settings.sql_auth_type
    if auth_type == SqlAuthType.SQL_AUTH:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["info"])
        auth_status.append("SQL Auth", style=COLORS["info"])
        auth_details = f"User: {settings.sql_username}" if settings.sql_username else ""
    elif auth_type == SqlAuthType.WINDOWS_AUTH:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["info"])
        auth_status.append("Windows Auth", style=COLORS["info"])
        auth_details = "Integrated Security"
    elif auth_type == SqlAuthType.AZURE_AD_INTERACTIVE:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["accent"])
        auth_status.append("Azure AD Interactive", style=COLORS["accent"])
        auth_details = "Browser login"
    elif auth_type == SqlAuthType.AZURE_AD_SERVICE_PRINCIPAL:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["accent"])
        auth_status.append("Azure AD SP", style=COLORS["accent"])
        auth_details = f"App: {settings.azure_client_id[:8]}..." if settings.azure_client_id else ""
    elif auth_type == SqlAuthType.AZURE_AD_MANAGED_IDENTITY:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["accent"])
        auth_status.append("Managed Identity", style=COLORS["accent"])
        auth_details = "System/User-assigned"
    elif auth_type == SqlAuthType.AZURE_AD_DEFAULT:
        auth_status.append(f"{Icons.GEAR} ", style=COLORS["accent"])
        auth_status.append("Azure AD Default", style=COLORS["accent"])
        auth_details = "Auto-detect credentials"
    else:
        auth_status.append(f"{Icons.INFO} ", style=COLORS["gray_400"])
        auth_status.append(auth_type.value, style=COLORS["gray_400"])
        auth_details = ""
    table.add_row(f"{Icons.GEAR} Auth Type", auth_status, auth_details)

    # Read-only mode
    readonly_status = Text()
    if settings.mcp_mssql_readonly:
        readonly_status.append(f"{Icons.INFO} ", style=COLORS["info"])
        readonly_status.append("Enabled", style=COLORS["info"])
    else:
        readonly_status.append(f"{Icons.WARNING} ", style=COLORS["warning"])
        readonly_status.append("Disabled", style=COLORS["warning"])
    table.add_row(f"{Icons.GEAR} Read-Only", readonly_status, "")

    console.print(table)
    console.print()


def print_help_commands() -> None:
    """Print available commands using styled help panel."""
    console.print(create_help_panel())


async def list_provider_models(provider_type: str) -> list[str]:
    """List available models for a provider."""
    try:
        ptype = ProviderType(provider_type)
        provider = create_provider(provider_type=ptype)
        return await provider.list_models()
    except Exception as e:
        logger.error("list_provider_models_error", provider=provider_type, error=str(e))
        return []


def print_cache_stats(agent: ResearchAgent) -> None:
    """Print cache statistics with styled table."""
    stats = agent.get_cache_stats()
    table = create_status_table(show_header=True)
    table.add_column(f"{Icons.DATABASE} Metric", style=COLORS["accent"])
    table.add_column("Value", style=COLORS["white"])

    # Cache enabled status
    enabled_text = Text()
    if agent.cache_enabled:
        enabled_text.append(f"{Icons.CHECK} ", style=COLORS["success"])
        enabled_text.append("Enabled", style=COLORS["success"])
    else:
        enabled_text.append(f"{Icons.CROSS} ", style=COLORS["error"])
        enabled_text.append("Disabled", style=COLORS["error"])

    table.add_row("Cache Status", enabled_text)
    table.add_row("Entries", str(stats.size))
    table.add_row("Max Size", str(stats.max_size))
    table.add_row("TTL", f"{stats.ttl_seconds}s" if stats.ttl_seconds > 0 else "No expiration")
    table.add_row("Hits", f"[{COLORS['success']}]{stats.hits}[/]")
    table.add_row("Misses", f"[{COLORS['warning']}]{stats.misses}[/]")
    table.add_row("Hit Rate", f"[{COLORS['primary']}]{stats.to_dict()['hit_rate']}[/]")
    table.add_row("Evictions", str(stats.evictions))

    console.print(table)
    console.print()


def format_thinking_content(content: str) -> str:
    """
    Parse and format <think> tags from model responses.

    Extracts content within <think>...</think> tags and formats it
    with visual distinction from the main response.

    Args:
        content: Raw model response that may contain <think> tags

    Returns:
        Formatted content with thinking blocks styled differently
    """
    import re

    # Pattern to match <think>...</think> blocks (handles multiline)
    think_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)

    def replace_think(match: re.Match) -> str:
        thinking_text = match.group(1).strip()
        # Format thinking content with visual distinction
        lines = thinking_text.split("\n")
        formatted_lines = []
        for line in lines:
            formatted_lines.append(f"[{COLORS['gray_400']}]│ {line}[/]")
        thinking_block = "\n".join(formatted_lines)
        return f"\n[{COLORS['accent']}]{Icons.THINKING} Reasoning:[/]\n{thinking_block}\n"

    return think_pattern.sub(replace_think, content)


class ThinkingModeInput:
    """
    Custom input handler with Shift+Tab keyboard shortcut support.

    Uses prompt_toolkit for advanced keyboard handling while maintaining
    Rich console integration for styled output.
    """

    def __init__(self, console, thinking_mode: bool = False):
        """
        Initialize input handler.

        Args:
            console: Rich console for output
            thinking_mode: Initial thinking mode state
        """
        self.console = console
        self.thinking_mode = thinking_mode
        self._toggled_this_prompt = False

        # Create key bindings
        self.bindings = KeyBindings()

        @self.bindings.add(Keys.BackTab)  # Shift+Tab
        def handle_shift_tab(event):
            """Toggle thinking mode on Shift+Tab."""
            self._toggled_this_prompt = True
            self.thinking_mode = not self.thinking_mode
            # Display immediate feedback
            if self.thinking_mode:
                self.console.print(
                    f"\n[{COLORS['success']}]{Icons.THINKING} Thinking Mode ENABLED[/]"
                )
            else:
                self.console.print(
                    f"\n[{COLORS['gray_400']}]{Icons.THINKING} Thinking Mode DISABLED[/]"
                )

        # Create prompt session with key bindings
        self.session = PromptSession(key_bindings=self.bindings)

    def get_input(self, prompt_text: str = "") -> tuple[str, bool]:
        """
        Get user input with Shift+Tab support.

        Args:
            prompt_text: Optional prompt text (not used, we use Rich for prompt)

        Returns:
            Tuple of (user_input, thinking_mode_changed)
        """
        self._toggled_this_prompt = False

        # Show thinking mode hint if disabled
        if not self.thinking_mode and sys.stdin.isatty():
            self.console.print(
                f"[{COLORS['gray_600']}]Press Shift+Tab to enable Thinking Mode[/]", end="  "
            )

        try:
            # Get input using prompt_toolkit
            user_input = self.session.prompt("")
            return user_input, self._toggled_this_prompt
        except (EOFError, KeyboardInterrupt):
            return "", False

    def is_interactive(self) -> bool:
        """Check if running in interactive mode."""
        return sys.stdin.isatty()


async def run_chat_loop(
    provider_type: str | None = None,
    model: str | None = None,
    readonly: bool = False,
    stream: bool = False,
    cache_enabled: bool = True,
    explain_mode: bool = False,
    thinking_mode: bool = False,
    web_search_enabled: bool = False,
    rag_enabled: bool = False,
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
        thinking_mode: Enable step-by-step reasoning with <think> tags
        web_search_enabled: Enable built-in web search tool
        rag_enabled: Enable RAG knowledge base search tools
    """
    # Use configured provider if not specified
    effective_provider = provider_type or settings.llm_provider

    # Check provider connection
    status = await check_provider_status(effective_provider)
    if not status["available"]:
        error_msg = status.get("error", "Unknown error")
        if effective_provider == "ollama":
            console.print(error_message(f"Ollama is not available: {error_msg}"))
            console.print(
                f"  {Icons.ARROW_RIGHT} Please start Ollama: [{COLORS['accent']}]ollama serve[/]"
            )
        else:
            console.print(error_message(f"Foundry Local is not available: {error_msg}"))
            console.print(
                f"  {Icons.ARROW_RIGHT} Install: [{COLORS['accent']}]pip install foundry-local-sdk[/]"
            )
        raise typer.Exit(1)

    if not settings.mcp_mssql_path:
        console.print(warning_message("MCP_MSSQL_PATH is not set"))
        console.print(f"  {Icons.BULLET} SQL Server tools will not be available")
        console.print(f"  {Icons.BULLET} Set this in your .env file")
        console.print()

    # Validate authentication configuration
    auth_errors = settings.validate_auth_config()
    if auth_errors:
        console.print(warning_message("Authentication configuration issues:"))
        for err in auth_errors:
            console.print(f"  {Icons.BULLET} [{COLORS['warning']}]{err}[/]")
        console.print()

    # Load enabled MCP servers
    try:
        from src.mcp.client import MCPClientManager

        mcp_manager = MCPClientManager()
        enabled_servers = [s.name for s in mcp_manager.list_servers() if s.enabled]

        if enabled_servers:
            console.print(
                f"[{COLORS['gray_400']}]{Icons.GEAR} Loading MCP servers: {', '.join(enabled_servers)}[/]"
            )

        agent = ResearchAgent(
            provider_type=effective_provider,
            model_name=model,
            readonly=readonly,
            cache_enabled=cache_enabled,
            explain_mode=explain_mode,
            thinking_mode=thinking_mode,
            web_search_enabled=web_search_enabled,
            rag_enabled=rag_enabled,
            mcp_servers=enabled_servers,  # Load all enabled servers!
        )
    except Exception as e:
        console.print(error_message(f"Error creating agent: {e}"))
        raise typer.Exit(1)

    # Show mode status
    mode_info = []
    if cache_enabled:
        mode_info.append(f"[{COLORS['accent']}]cache[/] (max {settings.cache_max_size})")
    if explain_mode:
        mode_info.append(f"[{COLORS['info']}]explain mode[/]")
    if thinking_mode:
        mode_info.append(f"[{COLORS['primary']}]{Icons.THINKING} thinking mode[/]")
    if web_search_enabled:
        mode_info.append(f"[{COLORS['info']}]{Icons.SEARCH} web search[/]")
    if rag_enabled:
        mode_info.append(f"[{COLORS['accent']}]📚 RAG[/]")
    if readonly:
        mode_info.append(f"[{COLORS['warning']}]read-only[/]")
    if mode_info:
        console.print(f"[{COLORS['gray_400']}]{Icons.GEAR} Features: {', '.join(mode_info)}[/]")
    console.print()

    print_help_commands()

    # Create input handler with Shift+Tab support (only in interactive mode)
    input_handler = ThinkingModeInput(console, thinking_mode=thinking_mode)
    if input_handler.is_interactive():
        console.print(
            f"[{COLORS['gray_500']}]{Icons.INFO} Tip: Press Shift+Tab anytime to toggle Thinking Mode[/]"
        )

    # Establish MCP sessions once for the entire chat session
    async with agent:
        console.print(f"[{COLORS['success']}]{Icons.CHECK} MCP sessions established[/]")
        console.print()

        while True:
            try:
                # Get user input with styled prompt
                console.print()
                console.print(f"[{COLORS['accent_light']}]{Icons.USER} You[/]", end=" ")

                # Use custom input handler in interactive mode, fallback to Rich prompt otherwise
                if input_handler.is_interactive():
                    user_input, mode_toggled = input_handler.get_input()

                    # If thinking mode was toggled, recreate agent with new mode
                    if mode_toggled:
                        thinking_mode = input_handler.thinking_mode
                        try:
                            # Properly exit old agent context before creating new one
                            await agent.__aexit__(None, None, None)
                            agent = ResearchAgent(
                                provider_type=effective_provider,
                                model_name=model,
                                readonly=readonly,
                                cache_enabled=cache_enabled,
                                explain_mode=explain_mode,
                                thinking_mode=thinking_mode,
                                web_search_enabled=web_search_enabled,
                                rag_enabled=rag_enabled,
                                mcp_servers=enabled_servers,
                            )
                            # Re-enter the agent context since we created a new agent
                            await agent.__aenter__()
                        except Exception as e:
                            console.print(error_message(f"Failed to update agent: {e}"))
                        # Show updated prompt for new input
                        continue
                else:
                    user_input = Prompt.ask("")

                if not user_input.strip():
                    continue

                # Handle commands
                command = user_input.strip().lower()

                if command in ("quit", "exit", "q"):
                    console.print()
                    console.print(format_goodbye())
                    break

                if command == "clear":
                    await handle_clear_command(agent, console)
                    continue

                if command == "status":
                    await print_status_async(effective_provider)
                    continue

                if command == "cache":
                    await handle_cache_command(agent, console)
                    continue

                if command == "cache-clear":
                    await handle_cache_clear_command(agent, console)
                    continue

                if command.startswith("export"):
                    await handle_export_command(command, agent, console)
                    continue

                if command.startswith("history"):
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
                        continue

                    elif parts[1] == "save":
                        if agent.conversation.total_turns == 0:
                            console.print(warning_message("No conversation to save"))
                        else:
                            title = Prompt.ask(
                                f"[{COLORS['gray_400']}]Session title[/]", default=""
                            )
                            session_id = history.save_session(
                                agent.conversation,
                                title=title if title else None,
                                provider=effective_provider,
                                model=model or "",
                            )
                            console.print(success_message(f"Session saved: {session_id}"))
                        continue

                    elif parts[1] == "load" and len(parts) >= 3:
                        session_id = parts[2]
                        session = history.load_session(session_id)
                        if session:
                            # Restore conversation
                            agent.conversation = session.to_conversation()
                            console.print(
                                success_message(f"Session loaded: {session.metadata.title}")
                            )
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]{session.metadata.turn_count} turns restored[/]"
                            )
                        else:
                            console.print(error_message(f"Session not found: {session_id}"))
                        continue

                    elif parts[1] == "delete" and len(parts) >= 3:
                        session_id = parts[2]
                        if history.delete_session(session_id):
                            console.print(success_message(f"Session deleted: {session_id}"))
                        else:
                            console.print(error_message(f"Session not found: {session_id}"))
                        continue

                    else:
                        console.print(
                            info_message("Usage: history [list|save|load <id>|delete <id>]")
                        )
                        continue

                if command.startswith("db"):
                    parts = command.split()
                    db_manager = get_database_manager()

                    if len(parts) == 1:
                        # List databases
                        databases = db_manager.list_databases()
                        console.print()
                        table = create_database_table()

                        for db in databases:
                            mode_text = Text()
                            if db["readonly"]:
                                mode_text.append("RO", style=COLORS["info"])
                            else:
                                mode_text.append("RW", style=COLORS["warning"])

                            active_text = Text()
                            if db["active"]:
                                active_text.append(f"{Icons.CHECK} Yes", style=COLORS["success"])
                            else:
                                active_text.append("")

                            table.add_row(
                                db["name"],
                                db["host"],
                                db["database"],
                                mode_text,
                                active_text,
                            )
                        console.print(table)
                        continue

                    elif parts[1] == "switch" and len(parts) >= 3:
                        db_name = parts[2]
                        if db_manager.set_active(db_name):
                            db_config = db_manager.active
                            console.print(success_message(f"Switched to database: {db_name}"))
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Connection: {db_config.connection_string_display}[/]"
                            )
                            console.print(
                                warning_message("Restart chat to apply new database connection")
                            )
                        else:
                            console.print(error_message(f"Database not found: {db_name}"))
                        continue

                    elif parts[1] == "add":
                        console.print()
                        console.print(
                            f"[bold {COLORS['primary']}]{Icons.DATABASE} Add New Database Configuration[/]"
                        )
                        console.print(styled_divider())
                        console.print()

                        name = Prompt.ask(
                            f"[{COLORS['gray_400']}]Database name (unique identifier)[/]"
                        )
                        if not name:
                            console.print(error_message("Name is required"))
                            continue

                        host = Prompt.ask(
                            f"[{COLORS['gray_400']}]SQL Server host[/]", default="localhost"
                        )
                        port = int(Prompt.ask(f"[{COLORS['gray_400']}]Port[/]", default="1433"))
                        database = Prompt.ask(f"[{COLORS['gray_400']}]Database name[/]")
                        username = Prompt.ask(
                            f"[{COLORS['gray_400']}]Username (blank for Windows Auth)[/]",
                            default="",
                        )
                        password = ""
                        if username:
                            password = Prompt.ask(
                                f"[{COLORS['gray_400']}]Password[/]", password=True, default=""
                            )
                        readonly = (
                            Prompt.ask(
                                f"[{COLORS['gray_400']}]Read-only mode?[/]",
                                choices=["y", "n"],
                                default="n",
                            )
                            == "y"
                        )
                        description = Prompt.ask(
                            f"[{COLORS['gray_400']}]Description (optional)[/]", default=""
                        )

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
                            console.print(success_message(f"Database added: {name}"))
                        except Exception as e:
                            console.print(error_message(f"Failed to add database: {e}"))
                        continue

                    elif parts[1] == "remove" and len(parts) >= 3:
                        db_name = parts[2]
                        if db_manager.remove_database(db_name):
                            console.print(success_message(f"Database removed: {db_name}"))
                        else:
                            console.print(error_message(f"Cannot remove database: {db_name}"))
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}](default database cannot be removed)[/]"
                            )
                        continue

                    else:
                        console.print(
                            info_message("Usage: db [list|switch <name>|add|remove <name>]")
                        )
                        continue

                if command == "help":
                    await handle_help_command(console)
                    continue

                # Handle /mcp commands
                if command.startswith("/mcp") or command.startswith("mcp"):
                    from src.cli.mcp_commands import handle_mcp_command

                    # Normalize command to start with /mcp
                    normalized_cmd = command if command.startswith("/mcp") else f"/{command}"
                    handle_mcp_command(console, normalized_cmd)
                    continue

                # Handle /provider command - switch LLM provider
                if command.startswith("/provider"):
                    parts = command.split()
                    if len(parts) < 2:
                        console.print(info_message("Usage: /provider <ollama|foundry_local>"))
                        console.print(
                            f"  {Icons.BULLET} [{COLORS['gray_400']}]Current: {effective_provider}[/]"
                        )
                        continue

                    new_provider = parts[1].lower()
                    if new_provider not in ("ollama", "foundry_local"):
                        console.print(error_message(f"Unknown provider: {new_provider}"))
                        console.print(
                            f"  {Icons.BULLET} [{COLORS['gray_400']}]Available: ollama, foundry_local[/]"
                        )
                        continue

                    # Check if the new provider is available
                    new_status = await check_provider_status(new_provider)
                    if not new_status["available"]:
                        console.print(error_message(f"Provider not available: {new_provider}"))
                        if new_status.get("error"):
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]{new_status['error']}[/]"
                            )
                        continue

                    # Create new agent with the new provider
                    try:
                        # Properly exit old agent context before creating new one
                        await agent.__aexit__(None, None, None)
                        effective_provider = new_provider
                        model = new_status.get("model")  # Use provider's default/available model
                        agent = ResearchAgent(
                            provider_type=effective_provider,
                            model_name=model,
                            readonly=readonly,
                            cache_enabled=cache_enabled,
                            explain_mode=explain_mode,
                            thinking_mode=thinking_mode,
                            web_search_enabled=web_search_enabled,
                            rag_enabled=rag_enabled,
                            mcp_servers=enabled_servers,
                        )
                        console.print(success_message(f"Switched to {new_provider}"))
                        console.print(
                            f"  {Icons.BULLET} [{COLORS['gray_400']}]Model: {agent.provider.model_name}[/]"
                        )
                    except Exception as e:
                        console.print(error_message(f"Failed to switch provider: {e}"))
                    continue

                # Handle /models command - list available models (before /model to avoid conflict)
                if command == "/models":
                    console.print()
                    console.print(f"[bold {COLORS['primary']}]{Icons.DATABASE} Available Models[/]")
                    console.print(styled_divider())

                    # List models for both providers
                    for prov in ["ollama", "foundry_local"]:
                        prov_name = "Ollama" if prov == "ollama" else "Foundry Local"
                        console.print(f"\n[{COLORS['accent']}]{prov_name}[/]:")

                        models = await list_provider_models(prov)
                        if models:
                            for m in models[:15]:  # Limit to 15 models
                                is_current = (
                                    prov == effective_provider and m == agent.provider.model_name
                                )
                                if is_current:
                                    console.print(
                                        f"  {Icons.STAR} [{COLORS['success']}]{m}[/] (active)"
                                    )
                                else:
                                    console.print(f"  {Icons.BULLET} [{COLORS['gray_300']}]{m}[/]")
                            if len(models) > 15:
                                console.print(
                                    f"  [{COLORS['gray_500']}]... and {len(models) - 15} more[/]"
                                )
                        else:
                            console.print(
                                f"  [{COLORS['gray_500']}]Not available or no models found[/]"
                            )

                    console.print()
                    continue

                # Handle /model command - switch model
                if command.startswith(
                    "/model "
                ):  # Note: space after /model to differentiate from /models
                    parts = command.split(maxsplit=1)
                    if len(parts) < 2:
                        console.print(info_message("Usage: /model <model_name>"))
                        console.print(
                            f"  {Icons.BULLET} [{COLORS['gray_400']}]Current: {agent.provider.model_name}[/]"
                        )
                        console.print(
                            f"  {Icons.BULLET} [{COLORS['gray_400']}]Use '/models' to list available models[/]"
                        )
                        continue

                    new_model = parts[1].strip()

                    # Create new agent with the new model
                    try:
                        # Properly exit old agent context before creating new one
                        await agent.__aexit__(None, None, None)
                        agent = ResearchAgent(
                            provider_type=effective_provider,
                            model_name=new_model,
                            readonly=readonly,
                            cache_enabled=cache_enabled,
                            explain_mode=explain_mode,
                            thinking_mode=thinking_mode,
                            web_search_enabled=web_search_enabled,
                            rag_enabled=rag_enabled,
                            mcp_servers=enabled_servers,
                        )
                        model = new_model
                        console.print(success_message(f"Switched to model: {new_model}"))
                    except Exception as e:
                        console.print(error_message(f"Failed to switch model: {e}"))
                    continue

                # Handle /model with no args - show current model info
                if command == "/model":
                    console.print(info_message("Usage: /model <model_name>"))
                    console.print(
                        f"  {Icons.BULLET} [{COLORS['gray_400']}]Current provider: {effective_provider}[/]"
                    )
                    console.print(
                        f"  {Icons.BULLET} [{COLORS['gray_400']}]Current model: {agent.provider.model_name}[/]"
                    )
                    console.print(
                        f"  {Icons.BULLET} [{COLORS['gray_400']}]Use '/models' to list available models[/]"
                    )
                    continue

                # Handle /thinking command - toggle thinking mode
                if command == "/thinking":
                    thinking_mode = not thinking_mode
                    # Sync input handler state
                    input_handler.thinking_mode = thinking_mode
                    # Recreate agent with updated thinking mode
                    try:
                        # Properly exit old agent context before creating new one
                        await agent.__aexit__(None, None, None)
                        agent = ResearchAgent(
                            provider_type=effective_provider,
                            model_name=model,
                            readonly=readonly,
                            cache_enabled=cache_enabled,
                            explain_mode=explain_mode,
                            thinking_mode=thinking_mode,
                            web_search_enabled=web_search_enabled,
                            rag_enabled=rag_enabled,
                            mcp_servers=enabled_servers,
                        )
                        # Re-enter the agent context
                        await agent.__aenter__()
                        if thinking_mode:
                            console.print(
                                success_message(f"{Icons.THINKING} Thinking mode enabled")
                            )
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Model will show step-by-step reasoning in <think> tags[/]"
                            )
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Best with Qwen3 or DeepSeek-R1 models[/]"
                            )
                        else:
                            console.print(info_message("Thinking mode disabled"))
                    except Exception as e:
                        console.print(error_message(f"Failed to toggle thinking mode: {e}"))
                    continue

                # Handle /websearch command - toggle web search
                if command == "/websearch":
                    web_search_enabled = not web_search_enabled
                    # Recreate agent with updated web search mode
                    try:
                        # Properly exit old agent context before creating new one
                        await agent.__aexit__(None, None, None)
                        agent = ResearchAgent(
                            provider_type=effective_provider,
                            model_name=model,
                            readonly=readonly,
                            cache_enabled=cache_enabled,
                            explain_mode=explain_mode,
                            thinking_mode=thinking_mode,
                            web_search_enabled=web_search_enabled,
                            rag_enabled=rag_enabled,
                            mcp_servers=enabled_servers,
                        )
                        # Re-enter the agent context
                        await agent.__aenter__()
                        if web_search_enabled:
                            console.print(success_message(f"{Icons.SEARCH} Web search enabled"))
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Built-in: DuckDuckGo (always available)[/]"
                            )
                            # Check if Brave MCP is enabled
                            brave_enabled = any(
                                s.name == "brave-search" and s.enabled
                                for s in mcp_manager.list_servers()
                            )
                            if brave_enabled:
                                console.print(
                                    f"  {Icons.BULLET} [{COLORS['success']}]Brave Search MCP: Enabled[/]"
                                )
                            else:
                                console.print(
                                    f"  {Icons.BULLET} [{COLORS['gray_500']}]Brave Search MCP: Disabled (enable with '/mcp enable brave-search')[/]"
                                )
                        else:
                            console.print(info_message("Web search disabled"))
                    except Exception as e:
                        console.print(error_message(f"Failed to toggle web search: {e}"))
                    continue

                # Handle /rag command - toggle RAG knowledge base
                if command == "/rag":
                    rag_enabled = not rag_enabled
                    # Recreate agent with updated RAG mode
                    try:
                        # Properly exit old agent context before creating new one
                        await agent.__aexit__(None, None, None)
                        agent = ResearchAgent(
                            provider_type=effective_provider,
                            model_name=model,
                            readonly=readonly,
                            cache_enabled=cache_enabled,
                            explain_mode=explain_mode,
                            thinking_mode=thinking_mode,
                            web_search_enabled=web_search_enabled,
                            rag_enabled=rag_enabled,
                            mcp_servers=enabled_servers,
                        )
                        # Re-enter the agent context
                        await agent.__aenter__()
                        if rag_enabled:
                            console.print(success_message("📚 RAG knowledge base enabled"))
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Tools: search_knowledge_base, list_knowledge_sources, get_document[/]"
                            )
                            console.print(
                                f"  {Icons.BULLET} [{COLORS['gray_400']}]Uses SQL Server 2025 native vector search (LLM_BackEnd)[/]"
                            )
                        else:
                            console.print(info_message("RAG knowledge base disabled"))
                    except Exception as e:
                        console.print(error_message(f"Failed to toggle RAG: {e}"))
                    continue

                # Send to agent
                console.print()
                console.print(format_agent_response_header(), end="")

                if stream:
                    # Streaming mode - print chunks as they arrive
                    with console.status(thinking_status(), spinner="dots"):
                        async for chunk in agent.chat_stream(user_input):
                            # Clear the status on first chunk
                            console.print(chunk, end="")
                    console.print()  # Final newline

                    # Display token usage after streaming
                    stats = agent.get_last_response_stats()
                    token_usage = stats.get("token_usage")
                    if token_usage and token_usage.total_tokens > 0:
                        console.print(
                            format_token_usage(
                                prompt_tokens=token_usage.prompt_tokens,
                                completion_tokens=token_usage.completion_tokens,
                                total_tokens=token_usage.total_tokens,
                                duration_ms=stats.get("duration_ms", 0),
                            )
                        )
                else:
                    # Non-streaming mode - show spinner while waiting
                    with console.status(thinking_status(), spinner="dots"):
                        detailed_response = await agent.chat_with_details(user_input)
                    # Format thinking tags if present
                    response_content = detailed_response.content
                    if thinking_mode and "<think>" in response_content:
                        response_content = format_thinking_content(response_content)
                    console.print(response_content)

                    # Display token usage
                    if (
                        detailed_response.token_usage
                        and detailed_response.token_usage.total_tokens > 0
                    ):
                        console.print(
                            format_token_usage(
                                prompt_tokens=detailed_response.token_usage.prompt_tokens,
                                completion_tokens=detailed_response.token_usage.completion_tokens,
                                total_tokens=detailed_response.token_usage.total_tokens,
                                duration_ms=detailed_response.duration_ms,
                            )
                        )

            except KeyboardInterrupt:
                console.print()
                console.print(warning_message("Interrupted. Type 'quit' to exit."))
                continue

            except ResearchAgentError as e:
                console.print()
                console.print(error_message(f"Agent error: {e}"))
                continue

            except Exception as e:
                logger.exception("chat_loop_error")
                console.print()
                console.print(error_message(f"Unexpected error: {e}"))
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
    thinking: bool = typer.Option(
        False,
        "--thinking",
        "-t",
        help="Enable thinking mode (step-by-step reasoning with <think> tags)",
    ),
    web_search: bool = typer.Option(
        False,
        "--web-search",
        "-w",
        help="Enable web search (DuckDuckGo + Brave MCP if configured)",
    ),
    rag: bool = typer.Option(
        False,
        "--rag",
        "-k",
        help="Enable RAG knowledge base search (SQL Server 2025 vectors)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
    simple_banner: bool = typer.Option(
        False,
        "--simple",
        help="Use simplified banner (less ASCII art)",
    ),
) -> None:
    """Start an interactive chat session with the research agent."""
    if debug:
        setup_logging("DEBUG")

    effective_provider = provider or settings.llm_provider
    effective_model = model or ""
    print_welcome(effective_provider, effective_model, readonly)
    print_status_sync(effective_provider)

    try:
        asyncio.run(
            run_chat_loop(
                provider_type=provider,
                model=model,
                readonly=readonly,
                stream=stream,
                cache_enabled=not no_cache,
                explain_mode=explain,
                thinking_mode=thinking,
                web_search_enabled=web_search,
                rag_enabled=rag,
            )
        )
    except Exception as e:
        console.print(error_message(f"Fatal error: {e}"))
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
        with console.status(
            f"[bold {COLORS['primary']}]{Icons.THINKING} Running health checks...[/]"
        ):
            result = await run_health_checks(include_database=database)

        if json_output:
            console.print(json.dumps(result.to_dict(), indent=2))
        else:
            # Color-coded output
            status_colors = {
                HealthStatus.HEALTHY: COLORS["success"],
                HealthStatus.UNHEALTHY: COLORS["error"],
                HealthStatus.DEGRADED: COLORS["warning"],
                HealthStatus.UNKNOWN: COLORS["gray_500"],
            }
            status_icons = {
                HealthStatus.HEALTHY: Icons.CHECK,
                HealthStatus.UNHEALTHY: Icons.CROSS,
                HealthStatus.DEGRADED: Icons.WARNING,
                HealthStatus.UNKNOWN: Icons.INFO,
            }

            color = status_colors.get(result.status, COLORS["white"])
            icon = status_icons.get(result.status, Icons.INFO)
            console.print()
            console.print(
                f"[bold {COLORS['white']}]{Icons.LIGHTNING} System Health:[/] [{color}]{icon} {result.status.value.upper()}[/]"
            )
            console.print()

            # Create styled table for components
            table = create_status_table(show_header=True)
            table.add_column(f"{Icons.GEAR} Component", style=COLORS["accent"])
            table.add_column("Status")
            table.add_column("Message", style=COLORS["gray_400"])
            if verbose:
                table.add_column(f"{Icons.CLOCK} Latency")

            for component in result.components:
                comp_color = status_colors.get(component.status, COLORS["white"])
                icon = status_icons.get(component.status, Icons.INFO)
                status_text = Text()
                status_text.append(f"{icon} ", style=comp_color)
                status_text.append(component.status.value, style=comp_color)

                if verbose and component.latency_ms:
                    latency = f"{component.latency_ms:.0f}ms"
                    table.add_row(component.name, status_text, component.message, latency)
                else:
                    table.add_row(component.name, status_text, component.message)

            console.print(table)

            if verbose:
                console.print()
                console.print(f"[bold {COLORS['primary']}]{Icons.INFO} Details:[/]")
                for component in result.components:
                    if component.details:
                        console.print(f"\n  [{COLORS['accent']}]{component.name}:[/]")
                        for key, value in component.details.items():
                            if isinstance(value, list):
                                value = ", ".join(str(v) for v in value[:5])
                            console.print(f"    [{COLORS['gray_400']}]{key}:[/] {value}")

            console.print()

    try:
        asyncio.run(run_checks())
    except Exception as e:
        console.print(error_message(f"Health check failed: {e}"))
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
    console.print()
    console.print(f"[bold {COLORS['primary']}]{Icons.GEAR} Configuration Status[/]")
    console.print(styled_divider())
    console.print()
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
            console.print(error_message(f"{effective_provider} is not available"))
            if status.get("error"):
                console.print(f"  {Icons.BULLET} [{COLORS['gray_400']}]{status['error']}[/]")
            raise typer.Exit(1)

        try:
            agent = ResearchAgent(
                provider_type=provider,
                model_name=model,
                readonly=readonly,
                cache_enabled=not no_cache,
            )
            if stream:
                with console.status(thinking_status(), spinner="dots"):
                    async for chunk in agent.chat_stream(message):
                        console.print(chunk, end="")
                console.print()

                # Display token usage after streaming
                stats = agent.get_last_response_stats()
                token_usage = stats.get("token_usage")
                if token_usage and token_usage.total_tokens > 0:
                    console.print(
                        format_token_usage(
                            prompt_tokens=token_usage.prompt_tokens,
                            completion_tokens=token_usage.completion_tokens,
                            total_tokens=token_usage.total_tokens,
                            duration_ms=stats.get("duration_ms", 0),
                        )
                    )
            else:
                with console.status(thinking_status(), spinner="dots"):
                    detailed_response = await agent.chat_with_details(message)
                console.print(detailed_response.content)

                # Display token usage
                if detailed_response.token_usage and detailed_response.token_usage.total_tokens > 0:
                    console.print(
                        format_token_usage(
                            prompt_tokens=detailed_response.token_usage.prompt_tokens,
                            completion_tokens=detailed_response.token_usage.completion_tokens,
                            total_tokens=detailed_response.token_usage.total_tokens,
                            duration_ms=detailed_response.duration_ms,
                        )
                    )
        except Exception as e:
            console.print(error_message(f"Error: {e}"))
            raise typer.Exit(1)

    asyncio.run(run_query())


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
