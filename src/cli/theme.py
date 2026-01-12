"""
CLI Theme and Styling

Modern, clean visual theme for the Agent AI CLI interface.
Features a gradient color palette with cyan/blue accents.
"""

import random
from datetime import datetime

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# =============================================================================
# Color Palette - Modern Gradient (Cyan to Purple)
# =============================================================================
COLORS = {
    # Primary gradient
    "primary": "#06B6D4",  # Cyan
    "primary_dark": "#0891B2",  # Dark cyan
    "primary_light": "#22D3EE",  # Light cyan
    "accent": "#8B5CF6",  # Purple
    "accent_light": "#A78BFA",  # Light purple
    "accent_dark": "#7C3AED",  # Dark purple
    # Gradient stops
    "gradient_1": "#06B6D4",  # Cyan
    "gradient_2": "#14B8A6",  # Teal
    "gradient_3": "#8B5CF6",  # Purple
    # Neutral tones
    "white": "#F8FAFC",
    "gray_100": "#F1F5F9",
    "gray_200": "#E2E8F0",
    "gray_300": "#CBD5E1",
    "gray_400": "#94A3B8",
    "gray_500": "#64748B",
    "gray_600": "#475569",
    "gray_700": "#334155",
    "gray_800": "#1E293B",
    # Status colors
    "success": "#10B981",  # Emerald
    "warning": "#F59E0B",  # Amber
    "error": "#EF4444",  # Red
    "info": "#06B6D4",  # Cyan
    # Special
    "dim": "#64748B",
    "muted": "#94A3B8",
    "highlight": "#FCD34D",  # Yellow highlight
}


# =============================================================================
# Unicode Icons (Modern CLI Compatible)
# =============================================================================
class Icons:
    """Modern Unicode icons for a clean interface."""

    # Brand/Logo
    LOGO = "\u25c8"  # Diamond with dot
    BRAIN = "\u2609"  # Sun (represents AI/intelligence)

    # Status icons
    CHECK = "\u2713"  # Check mark
    CROSS = "\u2717"  # Ballot X
    WARNING = "\u25b2"  # Triangle up (warning)
    INFO = "\u25cf"  # Filled circle
    CIRCLE = "\u25cf"  # Black circle
    CIRCLE_EMPTY = "\u25cb"  # White circle
    DOT = "\u2022"  # Bullet

    # Navigation/Action
    ARROW_RIGHT = "\u2192"  # Right arrow
    ARROW_LEFT = "\u2190"  # Left arrow
    CHEVRON = "\u203a"  # Single right angle quote
    BULLET = "\u2022"  # Bullet
    STAR = "\u2605"  # Black star
    SPARKLE = "\u2727"  # White four pointed star

    # Chat/Communication
    USER = "\u25b8"  # Right-pointing triangle
    ROBOT = "\u25c6"  # Black diamond
    CHAT = "\u25b6"  # Right-pointing triangle
    THINKING = "\u22ef"  # Midline horizontal ellipsis

    # Database/Data
    DATABASE = "\u25a3"  # White square containing black small square
    TABLE = "\u2261"  # Identical to (three lines)
    QUERY = "\u25b7"  # Right-pointing triangle outline

    # System
    GEAR = "\u2699"  # Gear
    LIGHTNING = "\u2607"  # Lightning
    CLOCK = "\u25f4"  # White circle with upper left quadrant
    FOLDER = "\u25a1"  # White square
    SEARCH = "\u2315"  # Telephone recorder / search icon
    GLOBE = "\u25ce"  # Bullseye / web globe

    # Decorative
    DIAMOND = "\u25c6"  # Black diamond
    SQUARE = "\u25a0"  # Black square
    PIPE = "\u2502"  # Box drawings light vertical
    DASH = "\u2500"  # Box drawings light horizontal


# =============================================================================
# Rich Theme Configuration
# =============================================================================
THEME = Theme(
    {
        # Primary styles
        "primary": Style(color=COLORS["primary"]),
        "primary.bold": Style(color=COLORS["primary"], bold=True),
        "accent": Style(color=COLORS["accent"]),
        "accent.bold": Style(color=COLORS["accent"], bold=True),
        # Gradient styles
        "gradient1": Style(color=COLORS["gradient_1"]),
        "gradient2": Style(color=COLORS["gradient_2"]),
        "gradient3": Style(color=COLORS["gradient_3"]),
        # Text styles
        "heading": Style(color=COLORS["white"], bold=True),
        "subheading": Style(color=COLORS["gray_300"]),
        "muted": Style(color=COLORS["gray_400"]),
        "dim": Style(color=COLORS["dim"]),
        # Status styles
        "success": Style(color=COLORS["success"]),
        "warning": Style(color=COLORS["warning"]),
        "error": Style(color=COLORS["error"]),
        "info": Style(color=COLORS["info"]),
        # Chat styles
        "user": Style(color=COLORS["primary_light"], bold=True),
        "agent": Style(color=COLORS["accent"], bold=True),
        "system": Style(color=COLORS["gray_400"], italic=True),
        # UI elements
        "border": Style(color=COLORS["gray_600"]),
        "highlight": Style(color=COLORS["highlight"], bold=True),
        "command": Style(color=COLORS["primary"]),
    }
)


def create_console() -> Console:
    """Create a console instance with the custom theme."""
    return Console(theme=THEME, highlight=False)


# =============================================================================
# ASCII Art Logo and Banners
# =============================================================================

# Clean, modern "Agent AI" ASCII art logo
BANNER_ART = """
[gradient1]    ___                    __     ___   ____[/]
[gradient2]   /   | ____ ____  ____  / /_   /   | /  _/[/]
[gradient2]  / /| |/ __ `/ _ \\/ __ \\/ __/  / /| | / /  [/]
[gradient3] / ___ / /_/ /  __/ / / / /_   / ___ |/ /   [/]
[gradient3]/_/  |_\\__, /\\___/_/ /_/\\__/  /_/  |_/___/  [/]
[accent]       /____/[/]
"""

BANNER_SUBTITLE = "[dim]SQL Server Analytics with Local LLMs[/]"

BANNER_SIMPLE = f"""[gradient1]{Icons.LOGO}[/] [bold white]Agent AI[/] [dim]v2.0[/]"""


# =============================================================================
# Styled Components
# =============================================================================


def print_banner(console: Console) -> None:
    """Print the main application banner."""
    console.print()
    console.print(BANNER_ART)
    console.print(f"    {BANNER_SUBTITLE}")
    console.print()


def styled_header(text: str, subtitle: str | None = None) -> Panel:
    """Create a styled header panel."""
    content = Text()
    content.append(text, style="bold white")

    if subtitle:
        content.append("\n")
        content.append(subtitle, style=COLORS["gray_400"])

    return Panel(
        content,
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 2),
    )


def styled_divider(width: int = 50) -> Text:
    """Create a styled gradient divider line."""
    text = Text()
    segment = width // 3
    text.append(Icons.DASH * segment, style=COLORS["gradient_1"])
    text.append(Icons.DASH * segment, style=COLORS["gradient_2"])
    text.append(Icons.DASH * (width - 2 * segment), style=COLORS["gradient_3"])
    return text


def styled_status_indicator(status: str, message: str = "") -> Text:
    """Create a styled status indicator."""
    text = Text()

    if status == "success":
        text.append(f"{Icons.CHECK} ", style=COLORS["success"])
        text.append(message or "Ready", style=COLORS["success"])
    elif status == "error":
        text.append(f"{Icons.CROSS} ", style=COLORS["error"])
        text.append(message or "Error", style=COLORS["error"])
    elif status == "warning":
        text.append(f"{Icons.WARNING} ", style=COLORS["warning"])
        text.append(message or "Warning", style=COLORS["warning"])
    else:  # info
        text.append(f"{Icons.INFO} ", style=COLORS["info"])
        text.append(message or "Info", style=COLORS["info"])

    return text


def user_prompt() -> str:
    """Get the styled user prompt string."""
    return f"[{COLORS['primary_light']}]{Icons.USER}[/]"


def agent_prompt() -> Text:
    """Get the styled agent prompt."""
    text = Text()
    text.append(f"{Icons.ROBOT} ", style=COLORS["accent"])
    text.append("Agent", style=f"bold {COLORS['accent']}")
    return text


def command_hint(command: str, description: str) -> Text:
    """Create a styled command hint."""
    text = Text()
    text.append(f"  {Icons.CHEVRON} ", style=COLORS["gray_500"])
    text.append(command, style=f"bold {COLORS['primary']}")
    text.append("  ", style="")
    text.append(description, style=COLORS["gray_400"])
    return text


def create_status_table(show_header: bool = True) -> Table:
    """Create a styled status table."""
    table = Table(
        show_header=show_header,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
        expand=False,
    )
    return table


def create_data_table(title: str | None = None) -> Table:
    """Create a styled data display table."""
    table = Table(
        title=title,
        title_style=f"bold {COLORS['white']}",
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )
    return table


def format_timestamp(dt: datetime | None = None) -> str:
    """Format a timestamp with styling."""
    if dt is None:
        dt = datetime.now()
    return f"[{COLORS['gray_500']}]{dt.strftime('%H:%M:%S')}[/]"


# Creative thinking/processing messages
THINKING_MESSAGES = [
    "Thinking",
    "Processing",
    "Analyzing query",
    "Consulting the database",
    "Crunching numbers",
    "Brewing insights",
    "Connecting neurons",
    "Mining data",
    "Weaving patterns",
    "Decoding request",
]

QUERYING_MESSAGES = [
    "Querying database",
    "Running SQL",
    "Fetching data",
    "Executing query",
    "Reading tables",
    "Gathering results",
    "Scanning records",
]


def thinking_status(querying: bool = False) -> str:
    """Get the thinking status message."""
    if querying:
        msg = random.choice(QUERYING_MESSAGES)
        return f"[{COLORS['info']}]{Icons.DATABASE} {msg}[/]"
    msg = random.choice(THINKING_MESSAGES)
    return f"[{COLORS['accent']}]{Icons.THINKING} {msg}[/]"


def format_token_usage(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    duration_ms: float = 0.0,
) -> Text:
    """Format token usage as styled text."""
    text = Text()
    text.append(f"\n[{COLORS['gray_600']}]{Icons.DASH * 40}[/]\n")
    text.append(f"{Icons.LIGHTNING} ", style=COLORS["gray_500"])
    text.append(f"{prompt_tokens:,}", style=COLORS["info"])
    text.append(" in ", style=COLORS["gray_500"])
    text.append(f"{Icons.ARROW_RIGHT} ", style=COLORS["gray_600"])
    text.append(f"{completion_tokens:,}", style=COLORS["success"])
    text.append(" out ", style=COLORS["gray_500"])
    text.append(f"{Icons.DOT} ", style=COLORS["gray_600"])
    text.append(f"{total_tokens:,}", style=COLORS["primary"])
    text.append(" total", style=COLORS["gray_500"])
    if duration_ms > 0:
        text.append(f" {Icons.DOT} ", style=COLORS["gray_600"])
        text.append(f"{duration_ms / 1000:.1f}s", style=COLORS["gray_400"])
    return text


def success_message(text: str) -> Text:
    """Create a success message."""
    msg = Text()
    msg.append(f"{Icons.CHECK} ", style=COLORS["success"])
    msg.append(text, style=COLORS["success"])
    return msg


def error_message(text: str) -> Text:
    """Create an error message."""
    msg = Text()
    msg.append(f"{Icons.CROSS} ", style=COLORS["error"])
    msg.append(text, style=COLORS["error"])
    return msg


def warning_message(text: str) -> Text:
    """Create a warning message."""
    msg = Text()
    msg.append(f"{Icons.WARNING} ", style=COLORS["warning"])
    msg.append(text, style=COLORS["warning"])
    return msg


def info_message(text: str) -> Text:
    """Create an info message."""
    msg = Text()
    msg.append(f"{Icons.INFO} ", style=COLORS["info"])
    msg.append(text, style=COLORS["info"])
    return msg


# =============================================================================
# Welcome and Help Panels
# =============================================================================


def create_welcome_panel(provider: str, model: str = "", readonly: bool = False) -> Panel:
    """Create a minimal welcome panel with provider info."""
    provider_name = "Ollama" if provider == "ollama" else "Foundry Local"

    content = Text()

    # Status line
    content.append(f"{Icons.CHECK} ", style=COLORS["success"])
    content.append("Connected", style=COLORS["success"])
    content.append(" to ", style=COLORS["gray_400"])
    content.append(provider_name, style=f"bold {COLORS['primary']}")

    if model:
        content.append(f" ({model})", style=COLORS["gray_500"])

    if readonly:
        content.append(f"\n{Icons.INFO} ", style=COLORS["warning"])
        content.append("Read-only mode", style=COLORS["warning"])

    return Panel(
        content,
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )


def create_help_panel() -> Panel:
    """Create the help commands panel."""
    # Core commands (shown in pairs)
    core_commands = [
        ("quit", "Exit"),
        ("clear", "Clear history"),
        ("status", "Connection info"),
        ("cache", "Cache stats"),
        ("export", "Save conversation"),
        ("history", "Past sessions"),
    ]

    # Model/Provider commands
    config_commands = [
        ("/provider <name>", "Switch provider (ollama, foundry_local)"),
        ("/model <name>", "Switch model"),
        ("/models", "List available models"),
        ("/thinking", "Toggle thinking mode (step-by-step reasoning)"),
        ("/websearch", "Toggle web search (DuckDuckGo + Brave MCP)"),
    ]
    
    # MCP server management commands
    mcp_commands = [
        ("/mcp", "List all MCP servers"),
        ("/mcp status <name>", "Show server details"),
        ("/mcp add", "Add new server interactively"),
        ("/mcp enable <name>", "Enable server"),
        ("/mcp disable <name>", "Disable server"),
        ("/mcp remove <name>", "Remove server"),
    ]

    content = Text()
    content.append("Commands\n", style=f"bold {COLORS['white']}")

    for i, (cmd, desc) in enumerate(core_commands):
        if i > 0 and i % 2 == 0:
            content.append("\n")
        content.append(f"  {cmd}", style=f"bold {COLORS['primary']}")
        content.append(f" {desc}", style=COLORS["gray_400"])
        if i % 2 == 0 and i < len(core_commands) - 1:
            content.append("  |  ", style=COLORS["gray_600"])

    content.append("\n\n")
    content.append("Config Commands\n", style=f"bold {COLORS['white']}")

    for cmd, desc in config_commands:
        content.append(f"\n  {cmd}", style=f"bold {COLORS['accent']}")
        content.append(f"  {desc}", style=COLORS["gray_400"])
    
    content.append("\n\n")
    content.append("MCP Servers\n", style=f"bold {COLORS['white']}")
    
    for cmd, desc in mcp_commands:
        content.append(f"\n  {cmd}", style=f"bold {COLORS['primary']}")
        content.append(f"  {desc}", style=COLORS["gray_400"])

    content.append("\n\n  ")
    content.append("help", style=f"bold {COLORS['primary']}")
    content.append(" Show commands", style=COLORS["gray_400"])

    return Panel(
        content,
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )


def create_session_table() -> Table:
    """Create a styled session history table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )
    table.add_column("ID", style=COLORS["primary"], width=10)
    table.add_column("Title", style=COLORS["white"], width=35)
    table.add_column("Turns", style=COLORS["gray_400"], justify="right", width=6)
    table.add_column("Updated", style=COLORS["gray_500"], width=14)
    return table


def create_database_table() -> Table:
    """Create a styled database list table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )
    table.add_column("Name", style=COLORS["primary"], width=12)
    table.add_column("Host", style=COLORS["gray_300"], width=18)
    table.add_column("Database", style=COLORS["gray_300"], width=18)
    table.add_column("Mode", style=COLORS["gray_400"], width=8)
    table.add_column("Active", width=8)
    return table


# =============================================================================
# Chat Message Formatting
# =============================================================================


def format_user_message(message: str) -> Panel:
    """Format a user message with styling."""
    return Panel(
        message,
        title=f"[{COLORS['primary_light']}]You[/]",
        title_align="left",
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )


def format_agent_response_header() -> Text:
    """Format the agent response header."""
    text = Text()
    text.append(f"\n{Icons.ROBOT} ", style=COLORS["accent"])
    text.append("Agent", style=f"bold {COLORS['accent']}")
    text.append("\n", style="")
    return text


def format_goodbye() -> Panel:
    """Format the goodbye message."""
    content = Text()
    content.append(f"{Icons.STAR} ", style=COLORS["accent"])
    content.append("Session ended", style=COLORS["gray_300"])
    content.append(f" at {datetime.now().strftime('%H:%M:%S')}", style=COLORS["gray_500"])

    return Panel(
        content,
        border_style=COLORS["gray_700"],
        box=ROUNDED,
        padding=(0, 1),
    )


# =============================================================================
# Quick Status Line
# =============================================================================


def format_status_line(provider: str, model: str, db: str = "ResearchAnalytics") -> Text:
    """Create a compact status line for the prompt area."""
    text = Text()
    text.append(f"{Icons.CIRCLE} ", style=COLORS["success"])
    text.append(provider, style=COLORS["primary"])
    text.append(f" {Icons.DOT} ", style=COLORS["gray_600"])
    text.append(model, style=COLORS["gray_400"])
    text.append(f" {Icons.DOT} ", style=COLORS["gray_600"])
    text.append(db, style=COLORS["gray_400"])
    return text
