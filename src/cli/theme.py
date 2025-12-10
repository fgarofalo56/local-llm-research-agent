"""
CLI Theme and Styling

Defines the visual theme for the CLI interface with blue/white color scheme
and Unicode icons for a modern, professional appearance.
"""

from rich.console import Console
from rich.theme import Theme
from rich.style import Style
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED, HEAVY, DOUBLE, MINIMAL, SIMPLE
from rich import box
from typing import Optional
from datetime import datetime


# =============================================================================
# Color Palette - Blues and Whites
# =============================================================================
COLORS = {
    # Primary blues
    "primary": "#60A5FA",        # Bright blue
    "primary_dark": "#3B82F6",   # Medium blue
    "primary_darker": "#2563EB", # Deep blue
    "accent": "#38BDF8",         # Sky blue
    "accent_light": "#7DD3FC",   # Light sky blue

    # Neutral/whites
    "white": "#FFFFFF",
    "gray_100": "#F3F4F6",
    "gray_200": "#E5E7EB",
    "gray_300": "#D1D5DB",
    "gray_400": "#9CA3AF",
    "gray_500": "#6B7280",
    "gray_600": "#4B5563",

    # Status colors
    "success": "#34D399",        # Green
    "warning": "#FBBF24",        # Yellow
    "error": "#F87171",          # Red
    "info": "#60A5FA",           # Blue

    # Special
    "dim": "#64748B",
    "muted": "#94A3B8",
}


# =============================================================================
# Unicode Icons (CLI Compatible)
# =============================================================================
class Icons:
    """Unicode icons that work in most modern terminals."""

    # Status icons
    CHECK = "\u2714"          # Heavy check mark
    CROSS = "\u2718"          # Heavy ballot X
    WARNING = "\u26A0"        # Warning sign
    INFO = "\u2139"           # Information
    CIRCLE = "\u25CF"         # Black circle
    CIRCLE_EMPTY = "\u25CB"   # White circle

    # Navigation/Action
    ARROW_RIGHT = "\u279C"    # Heavy round-tipped rightwards arrow
    ARROW_DOWN = "\u25BC"     # Down-pointing triangle
    BULLET = "\u2022"         # Bullet
    STAR = "\u2605"           # Black star
    SPARKLE = "\u2728"        # Sparkles

    # Chat/Communication
    USER = "\u263A"           # Smiling face (simple)
    ROBOT = "\u2699"          # Gear (representing AI)
    CHAT = "\u25B6"           # Right-pointing triangle
    THINKING = "\u2026"       # Ellipsis

    # Database/Data
    DATABASE = "\u229E"       # Squared plus (grid-like)
    TABLE = "\u25A6"          # Square with orthogonal crosshatch
    SEARCH = "\u25B7"         # Right-pointing triangle outline

    # System
    GEAR = "\u2699"           # Gear
    LIGHTNING = "\u26A1"      # High voltage
    CLOCK = "\u23F1"          # Stopwatch
    FOLDER = "\u25A1"         # White square (folder-like)

    # Decorative
    DIAMOND = "\u25C6"        # Black diamond
    SQUARE = "\u25A0"         # Black square
    DOT = "\u00B7"            # Middle dot
    PIPE = "\u2502"           # Box drawings light vertical


# =============================================================================
# Rich Theme Configuration
# =============================================================================
THEME = Theme({
    # Primary styles
    "primary": Style(color=COLORS["primary"]),
    "primary.bold": Style(color=COLORS["primary"], bold=True),
    "accent": Style(color=COLORS["accent"]),
    "accent.bold": Style(color=COLORS["accent"], bold=True),

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
    "user": Style(color=COLORS["accent_light"], bold=True),
    "agent": Style(color=COLORS["primary"], bold=True),
    "system": Style(color=COLORS["gray_400"], italic=True),

    # UI elements
    "border": Style(color=COLORS["primary_dark"]),
    "highlight": Style(color=COLORS["accent"], bold=True),
    "command": Style(color=COLORS["accent"]),
})


# Create themed console
def create_console() -> Console:
    """Create a console instance with the custom theme."""
    return Console(theme=THEME, highlight=False)


# =============================================================================
# ASCII Art and Banners
# =============================================================================
BANNER_ART = f"""
[primary]    ╭──────────────────────────────────────────────────────────╮[/]
[primary]    │[/] [accent.bold]  _     _     __  __   ____                          [/] [primary]│[/]
[primary]    │[/] [accent.bold] | |   | |   |  \/  | |  _ \ ___  ___  ___  __ _ _ __ [/] [primary]│[/]
[primary]    │[/] [accent.bold] | |   | |   | |\/| | | |_) / _ \/ __|/ _ \/ _` | '__|[/] [primary]│[/]
[primary]    │[/] [accent.bold] | |___| |___| |  | | |  _ <  __/\__ \  __/ (_| | |   [/] [primary]│[/]
[primary]    │[/] [accent.bold] |_____|_____|_|  |_| |_| \_\___||___/\___|\__,_|_|   [/] [primary]│[/]
[primary]    │[/]                                                        [primary]│[/]
[primary]    │[/]  [white]Local LLM Research Analytics Agent[/]                     [primary]│[/]
[primary]    │[/]  [muted]Query your SQL Server data using natural language[/]      [primary]│[/]
[primary]    ╰──────────────────────────────────────────────────────────╯[/]
"""

BANNER_SIMPLE = f"""
[primary]╭─────────────────────────────────────────────────────────────────╮[/]
[primary]│[/]  [accent.bold]{Icons.DATABASE} LLM Research Agent[/]  [muted]v1.0[/]                               [primary]│[/]
[primary]│[/]  [dim]Chat with your SQL Server data using natural language[/]       [primary]│[/]
[primary]╰─────────────────────────────────────────────────────────────────╯[/]
"""


# =============================================================================
# Styled Components
# =============================================================================
def styled_header(text: str, subtitle: Optional[str] = None) -> Panel:
    """Create a styled header panel."""
    content = Text()
    content.append(f"{Icons.DIAMOND} ", style=COLORS["accent"])
    content.append(text, style="bold white")

    if subtitle:
        content.append("\n")
        content.append(f"  {subtitle}", style=COLORS["gray_400"])

    return Panel(
        content,
        border_style=COLORS["primary_dark"],
        box=ROUNDED,
        padding=(0, 2),
    )


def styled_divider(char: str = "─", width: int = 60) -> Text:
    """Create a styled divider line."""
    text = Text()
    text.append(char * width, style=COLORS["gray_600"])
    return text


def styled_status_indicator(status: str, message: str = "") -> Text:
    """Create a styled status indicator."""
    text = Text()

    if status == "success":
        text.append(f" {Icons.CHECK} ", style=COLORS["success"])
        text.append(message or "Ready", style=COLORS["success"])
    elif status == "error":
        text.append(f" {Icons.CROSS} ", style=COLORS["error"])
        text.append(message or "Error", style=COLORS["error"])
    elif status == "warning":
        text.append(f" {Icons.WARNING} ", style=COLORS["warning"])
        text.append(message or "Warning", style=COLORS["warning"])
    else:  # info
        text.append(f" {Icons.INFO} ", style=COLORS["info"])
        text.append(message or "Info", style=COLORS["info"])

    return text


def user_prompt() -> str:
    """Get the styled user prompt string."""
    return f"[{COLORS['accent_light']}]{Icons.USER} You[/]"


def agent_prompt() -> Text:
    """Get the styled agent prompt."""
    text = Text()
    text.append(f"{Icons.ROBOT} ", style=COLORS["primary"])
    text.append("Agent", style=f"bold {COLORS['primary']}")
    return text


def command_hint(command: str, description: str) -> Text:
    """Create a styled command hint."""
    text = Text()
    text.append(f"  {Icons.BULLET} ", style=COLORS["gray_500"])
    text.append(command, style=f"bold {COLORS['accent']}")
    text.append(f"  {Icons.DOT} ", style=COLORS["gray_600"])
    text.append(description, style=COLORS["gray_400"])
    return text


def create_status_table(show_header: bool = True) -> Table:
    """Create a styled status table."""
    table = Table(
        show_header=show_header,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
        expand=False,
    )
    return table


def create_data_table(title: Optional[str] = None) -> Table:
    """Create a styled data display table."""
    table = Table(
        title=title,
        title_style=f"bold {COLORS['primary']}",
        header_style=f"bold {COLORS['accent']}",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
    )
    return table


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a timestamp with styling."""
    if dt is None:
        dt = datetime.now()
    return f"[{COLORS['gray_500']}]{dt.strftime('%H:%M:%S')}[/]"


def thinking_status() -> str:
    """Get the thinking status message."""
    return f"[bold {COLORS['primary']}]{Icons.THINKING} Thinking[/]"


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
    """Create the welcome panel with provider info."""
    provider_name = "Ollama" if provider == "ollama" else "Foundry Local"

    content = Text()
    content.append(f"\n  {Icons.LIGHTNING} ", style=COLORS["accent"])
    content.append("Provider: ", style=COLORS["gray_400"])
    content.append(f"{provider_name}", style=f"bold {COLORS['accent']}")

    if model:
        content.append(f"\n  {Icons.GEAR} ", style=COLORS["primary"])
        content.append("Model: ", style=COLORS["gray_400"])
        content.append(f"{model}", style=COLORS["primary"])

    if readonly:
        content.append(f"\n  {Icons.INFO} ", style=COLORS["warning"])
        content.append("Mode: ", style=COLORS["gray_400"])
        content.append("Read-only", style=COLORS["warning"])

    content.append(f"\n\n  {Icons.BULLET} ", style=COLORS["gray_500"])
    content.append("Type ", style=COLORS["gray_400"])
    content.append("help", style=f"bold {COLORS['accent']}")
    content.append(" for commands, ", style=COLORS["gray_400"])
    content.append("quit", style=f"bold {COLORS['accent']}")
    content.append(" to exit\n", style=COLORS["gray_400"])

    return Panel(
        content,
        title=f"[bold {COLORS['white']}]{Icons.SPARKLE} Ready[/]",
        title_align="left",
        border_style=COLORS["primary_dark"],
        box=ROUNDED,
        padding=(0, 1),
    )


def create_help_panel() -> Panel:
    """Create the help commands panel."""
    commands = [
        ("quit", "q", "Exit the chat session"),
        ("clear", "", "Clear conversation history"),
        ("status", "", "Show connection status"),
        ("cache", "", "Show cache statistics"),
        ("cache-clear", "", "Clear response cache"),
        ("export [fmt]", "", "Export conversation (json/csv/md)"),
        ("history", "", "List saved sessions"),
        ("history save", "", "Save current session"),
        ("history load <id>", "", "Load a saved session"),
        ("db", "", "List configured databases"),
        ("db switch <name>", "", "Switch database"),
        ("help", "", "Show this help"),
    ]

    content = Text()

    for cmd, shortcut, desc in commands:
        content.append(f"\n  {Icons.ARROW_RIGHT} ", style=COLORS["primary"])
        content.append(cmd, style=f"bold {COLORS['accent']}")
        if shortcut:
            content.append(f" ({shortcut})", style=COLORS["gray_500"])
        content.append("\n    ", style="")
        content.append(desc, style=COLORS["gray_400"])

    content.append("\n")

    return Panel(
        content,
        title=f"[bold {COLORS['white']}]{Icons.INFO} Commands[/]",
        title_align="left",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
    )


def create_session_table() -> Table:
    """Create a styled session history table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
    )
    table.add_column(f"{Icons.FOLDER} ID", style=COLORS["accent"], width=10)
    table.add_column("Title", style=COLORS["white"], width=35)
    table.add_column("Turns", style=COLORS["gray_400"], justify="right", width=6)
    table.add_column(f"{Icons.CLOCK} Updated", style=COLORS["gray_500"], width=14)
    return table


def create_database_table() -> Table:
    """Create a styled database list table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
    )
    table.add_column(f"{Icons.DATABASE} Name", style=COLORS["accent"], width=12)
    table.add_column("Host", style=COLORS["gray_300"], width=18)
    table.add_column("Database", style=COLORS["gray_300"], width=18)
    table.add_column("Mode", style=COLORS["gray_400"], width=6)
    table.add_column("Active", width=8)
    return table


# =============================================================================
# Chat Message Formatting
# =============================================================================
def format_user_message(message: str) -> Panel:
    """Format a user message with styling."""
    return Panel(
        message,
        title=f"[{COLORS['accent_light']}]{Icons.USER} You[/]",
        title_align="left",
        border_style=COLORS["accent"],
        box=ROUNDED,
        padding=(0, 1),
    )


def format_agent_response_header() -> Text:
    """Format the agent response header."""
    text = Text()
    text.append(f"\n{Icons.ROBOT} ", style=COLORS["primary"])
    text.append("Agent", style=f"bold {COLORS['primary']}")
    text.append(f"  {Icons.DOT}  ", style=COLORS["gray_600"])
    return text


def format_goodbye() -> Panel:
    """Format the goodbye message."""
    content = Text()
    content.append(f"\n  {Icons.STAR} ", style=COLORS["accent"])
    content.append("Thank you for using LLM Research Agent!", style=COLORS["gray_300"])
    content.append(f"\n  {Icons.BULLET} Session ended at {datetime.now().strftime('%H:%M:%S')}\n",
                  style=COLORS["gray_500"])

    return Panel(
        content,
        title=f"[{COLORS['warning']}]{Icons.CHECK} Goodbye[/]",
        title_align="left",
        border_style=COLORS["gray_600"],
        box=ROUNDED,
        padding=(0, 1),
    )
