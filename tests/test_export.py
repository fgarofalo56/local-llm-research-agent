"""
Tests for Export Utilities

Tests export functionality for conversations and data to various formats.
"""

import json
import os
import tempfile
from datetime import datetime

import pytest

from src.models.chat import ChatMessage, Conversation, ConversationTurn
from src.utils.export import (
    ExportError,
    export_conversation_to_csv,
    export_response_data,
    export_to_csv,
    export_to_json,
    export_to_markdown,
    extract_table_from_response,
    generate_export_filename,
)


class TestExtractTableFromResponse:
    """Tests for markdown table extraction."""

    def test_extract_simple_table(self):
        """Test extracting a simple markdown table."""
        response = """
Here is the data:

| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |

That's all the data.
"""
        result = extract_table_from_response(response)
        assert result is not None
        assert len(result) == 2
        assert result[0] == {"Name": "Alice", "Age": "30", "City": "NYC"}
        assert result[1] == {"Name": "Bob", "Age": "25", "City": "LA"}

    def test_extract_aligned_table(self):
        """Test extracting a table with alignment markers."""
        response = """
| Left | Center | Right |
|:-----|:------:|------:|
| L1 | C1 | R1 |
| L2 | C2 | R2 |
"""
        result = extract_table_from_response(response)
        assert result is not None
        assert len(result) == 2

    def test_no_table_returns_none(self):
        """Test that text without tables returns None."""
        response = "This is just plain text without any tables."
        result = extract_table_from_response(response)
        assert result is None

    def test_malformed_table_returns_none(self):
        """Test that malformed tables return None."""
        response = """
| Header |
Not a proper table
"""
        result = extract_table_from_response(response)
        assert result is None


class TestExportToJson:
    """Tests for JSON export functionality."""

    def test_export_list_of_dicts(self):
        """Test exporting a list of dictionaries."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = export_to_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_export_dict(self):
        """Test exporting a single dictionary."""
        data = {"key": "value", "number": 42}
        result = export_to_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_export_conversation(self):
        """Test exporting a Conversation object."""
        conv = Conversation()
        turn = ConversationTurn(
            user_message=ChatMessage.user("Hello"),
            assistant_message=ChatMessage.assistant("Hi there!"),
            duration_ms=100,
        )
        conv.add_turn(turn)

        result = export_to_json(conv)
        parsed = json.loads(result)

        assert "metadata" in parsed
        assert "turns" in parsed
        assert parsed["metadata"]["total_turns"] == 1
        assert len(parsed["turns"]) == 1
        assert parsed["turns"][0]["user"] == "Hello"
        assert parsed["turns"][0]["assistant"] == "Hi there!"

    def test_export_to_file(self):
        """Test exporting to a file."""
        data = {"test": "data"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            export_to_json(data, filepath)
            assert os.path.exists(filepath)

            with open(filepath, encoding="utf-8") as f:
                content = json.load(f)
            assert content == data
        finally:
            os.unlink(filepath)


class TestExportToCsv:
    """Tests for CSV export functionality."""

    def test_export_list_of_dicts(self):
        """Test exporting a list of dictionaries."""
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
        result = export_to_csv(data)

        lines = result.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows
        assert "name" in lines[0]
        assert "age" in lines[0]
        assert "Alice" in lines[1]

    def test_empty_data_raises_error(self):
        """Test that empty data raises an error."""
        with pytest.raises(ExportError):
            export_to_csv([])

    def test_non_list_raises_error(self):
        """Test that non-list data raises an error."""
        with pytest.raises(ExportError):
            export_to_csv({"not": "a list"})  # type: ignore

    def test_export_to_file(self):
        """Test exporting to a file."""
        data = [{"col1": "val1", "col2": "val2"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            export_to_csv(data, filepath)
            assert os.path.exists(filepath)

            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            assert "col1" in content
            assert "val1" in content
        finally:
            os.unlink(filepath)


class TestExportConversationToCsv:
    """Tests for conversation CSV export."""

    def test_export_conversation(self):
        """Test exporting conversation to CSV."""
        conv = Conversation()
        turn1 = ConversationTurn(
            user_message=ChatMessage.user("Question 1"),
            assistant_message=ChatMessage.assistant("Answer 1"),
            duration_ms=100,
        )
        turn2 = ConversationTurn(
            user_message=ChatMessage.user("Question 2"),
            assistant_message=ChatMessage.assistant("Answer 2"),
            duration_ms=200,
        )
        conv.add_turn(turn1)
        conv.add_turn(turn2)

        result = export_conversation_to_csv(conv)
        lines = result.strip().split("\n")

        assert len(lines) == 3  # Header + 2 rows
        assert "user_message" in lines[0]
        assert "assistant_response" in lines[0]


class TestExportToMarkdown:
    """Tests for Markdown export functionality."""

    def test_export_conversation(self):
        """Test exporting conversation to Markdown."""
        conv = Conversation()
        turn = ConversationTurn(
            user_message=ChatMessage.user("Hello"),
            assistant_message=ChatMessage.assistant("Hi there!"),
            duration_ms=100,
        )
        conv.add_turn(turn)

        result = export_to_markdown(conv, title="Test Export")

        assert "# Test Export" in result
        assert "**User:**" in result
        assert "Hello" in result
        assert "**Assistant:**" in result
        assert "Hi there!" in result
        assert "Turn 1" in result

    def test_export_to_file(self):
        """Test exporting to a file."""
        conv = Conversation()
        turn = ConversationTurn(
            user_message=ChatMessage.user("Test"),
            assistant_message=ChatMessage.assistant("Response"),
            duration_ms=50,
        )
        conv.add_turn(turn)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            filepath = f.name

        try:
            export_to_markdown(conv, filepath)
            assert os.path.exists(filepath)

            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            assert "Test" in content
            assert "Response" in content
        finally:
            os.unlink(filepath)


class TestExportResponseData:
    """Tests for extracting and exporting table data from responses."""

    def test_export_table_to_json(self):
        """Test extracting table and exporting to JSON."""
        response = """
| ID | Name |
|----|------|
| 1 | Alice |
| 2 | Bob |
"""
        result = export_response_data(response, format="json")
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_export_table_to_csv(self):
        """Test extracting table and exporting to CSV."""
        response = """
| ID | Name |
|----|------|
| 1 | Alice |
"""
        result = export_response_data(response, format="csv")
        assert result is not None
        assert "ID" in result
        assert "Alice" in result

    def test_no_table_returns_none(self):
        """Test that no table returns None."""
        response = "No tables here"
        result = export_response_data(response, format="json")
        assert result is None

    def test_unsupported_format_raises_error(self):
        """Test that unsupported format raises error."""
        response = "| A |\n|---|\n| 1 |"
        with pytest.raises(ExportError):
            export_response_data(response, format="xml")


class TestGenerateExportFilename:
    """Tests for filename generation."""

    def test_generates_timestamped_filename(self):
        """Test that filename includes timestamp."""
        filename = generate_export_filename("test", "json")
        assert filename.startswith("test_")
        assert filename.endswith(".json")
        assert len(filename) > len("test_.json")

    def test_different_formats(self):
        """Test different format extensions."""
        assert generate_export_filename("export", "csv").endswith(".csv")
        assert generate_export_filename("export", "md").endswith(".md")
        assert generate_export_filename("export", "json").endswith(".json")
