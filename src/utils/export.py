"""
Export Utilities

Provides functionality to export conversations and query results
to various formats including JSON, CSV, and Markdown.
"""

import csv
import json
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from src.models.chat import Conversation
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExportError(Exception):
    """Error during export operation."""

    pass


def extract_table_from_response(response: str) -> list[dict[str, Any]] | None:
    """
    Extract tabular data from a response containing markdown tables.

    Attempts to parse markdown tables in the response and convert
    them to a list of dictionaries.

    Args:
        response: Response text that may contain markdown tables

    Returns:
        List of dictionaries representing table rows, or None if no table found
    """
    # Look for markdown table pattern
    # Header row: | col1 | col2 | col3 |
    # Separator:  |------|------|------|
    # Data rows:  | val1 | val2 | val3 |
    table_pattern = r'\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)'
    match = re.search(table_pattern, response)

    if not match:
        return None

    try:
        # Parse header
        header_text = match.group(1)
        headers = [h.strip() for h in header_text.split('|') if h.strip()]

        # Parse data rows
        data_text = match.group(2)
        rows = []
        for line in data_text.strip().split('\n'):
            if line.strip():
                values = [v.strip() for v in line.split('|') if v.strip()]
                if len(values) == len(headers):
                    row = dict(zip(headers, values))
                    rows.append(row)

        return rows if rows else None

    except Exception as e:
        logger.debug("table_extraction_failed", error=str(e))
        return None


def export_to_json(
    data: list[dict[str, Any]] | dict[str, Any] | Conversation,
    filepath: str | Path | None = None,
    indent: int = 2,
) -> str:
    """
    Export data to JSON format.

    Args:
        data: Data to export (list of dicts, dict, or Conversation)
        filepath: Optional file path to save (if None, returns string)
        indent: JSON indentation level

    Returns:
        JSON string representation

    Raises:
        ExportError: If export fails
    """
    try:
        # Convert Conversation to dict
        if isinstance(data, Conversation):
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_turns": data.total_turns,
                    "total_duration_ms": data.total_duration_ms,
                },
                "turns": [
                    {
                        "user": turn.user_message.content,
                        "assistant": turn.assistant_message.content,
                        "duration_ms": turn.duration_ms,
                        "timestamp": turn.user_message.timestamp.isoformat(),
                    }
                    for turn in data.turns
                ],
            }
        else:
            export_data = data

        json_str = json.dumps(export_data, indent=indent, ensure_ascii=False)

        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str, encoding="utf-8")
            logger.info("export_to_json", filepath=str(path))

        return json_str

    except Exception as e:
        raise ExportError(f"Failed to export to JSON: {e}") from e


def export_to_csv(
    data: list[dict[str, Any]],
    filepath: str | Path | None = None,
) -> str:
    """
    Export tabular data to CSV format.

    Args:
        data: List of dictionaries to export
        filepath: Optional file path to save (if None, returns string)

    Returns:
        CSV string representation

    Raises:
        ExportError: If export fails or data is not tabular
    """
    if not data:
        raise ExportError("No data to export")

    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ExportError("Data must be a list of dictionaries for CSV export")

    try:
        output = StringIO()
        # Get all unique headers across all rows
        headers = list(dict.fromkeys(
            key for row in data for key in row.keys()
        ))

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

        csv_str = output.getvalue()

        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(csv_str, encoding="utf-8")
            logger.info("export_to_csv", filepath=str(path))

        return csv_str

    except Exception as e:
        raise ExportError(f"Failed to export to CSV: {e}") from e


def export_conversation_to_csv(
    conversation: Conversation,
    filepath: str | Path | None = None,
) -> str:
    """
    Export conversation to CSV format.

    Args:
        conversation: Conversation to export
        filepath: Optional file path to save

    Returns:
        CSV string representation
    """
    data = [
        {
            "timestamp": turn.user_message.timestamp.isoformat(),
            "user_message": turn.user_message.content,
            "assistant_response": turn.assistant_message.content,
            "duration_ms": turn.duration_ms,
        }
        for turn in conversation.turns
    ]
    return export_to_csv(data, filepath)


def export_to_markdown(
    conversation: Conversation,
    filepath: str | Path | None = None,
    title: str = "Chat Export",
) -> str:
    """
    Export conversation to Markdown format.

    Args:
        conversation: Conversation to export
        filepath: Optional file path to save
        title: Document title

    Returns:
        Markdown string representation
    """
    try:
        lines = [
            f"# {title}",
            "",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total turns:** {conversation.total_turns}",
            f"**Total duration:** {conversation.total_duration_ms:.0f}ms",
            "",
            "---",
            "",
        ]

        for i, turn in enumerate(conversation.turns, 1):
            timestamp = turn.user_message.timestamp.strftime("%H:%M:%S")
            lines.extend([
                f"## Turn {i} ({timestamp})",
                "",
                "**User:**",
                turn.user_message.content,
                "",
                "**Assistant:**",
                turn.assistant_message.content,
                "",
                f"*Response time: {turn.duration_ms:.0f}ms*",
                "",
                "---",
                "",
            ])

        md_str = "\n".join(lines)

        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(md_str, encoding="utf-8")
            logger.info("export_to_markdown", filepath=str(path))

        return md_str

    except Exception as e:
        raise ExportError(f"Failed to export to Markdown: {e}") from e


def export_response_data(
    response: str,
    format: str = "json",
    filepath: str | Path | None = None,
) -> str | None:
    """
    Extract and export tabular data from a response.

    Attempts to find and extract markdown tables from the response
    and export them in the specified format.

    Args:
        response: Response text containing data
        format: Export format ('json' or 'csv')
        filepath: Optional file path to save

    Returns:
        Exported string, or None if no tabular data found

    Raises:
        ExportError: If export fails
    """
    data = extract_table_from_response(response)

    if data is None:
        return None

    if format.lower() == "json":
        return export_to_json(data, filepath)
    elif format.lower() == "csv":
        return export_to_csv(data, filepath)
    else:
        raise ExportError(f"Unsupported format: {format}")


def generate_export_filename(
    prefix: str = "export",
    format: str = "json",
) -> str:
    """
    Generate a timestamped export filename.

    Args:
        prefix: Filename prefix
        format: File extension/format

    Returns:
        Filename string like "export_20240101_120000.json"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{format}"
