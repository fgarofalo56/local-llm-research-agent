"""
Tests for Chat and SQL Result Models

Tests the Pydantic models in src/models/chat.py and src/models/sql_results.py.
"""

import pytest
from datetime import datetime

from src.models.chat import (
    MessageRole,
    ChatMessage,
    ToolCall,
    ConversationTurn,
    Conversation,
    AgentResponse,
)
from src.models.sql_results import (
    ColumnInfo,
    TableInfo,
    QueryResult,
    DatabaseSchema,
)


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_message_roles(self):
        """Test all message roles exist."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.TOOL == "tool"


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_create_chat_message(self):
        """Test creating a basic chat message."""
        msg = ChatMessage(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_user_factory_method(self):
        """Test user message factory method."""
        msg = ChatMessage.user("Hello there", source="cli")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello there"
        assert msg.metadata == {"source": "cli"}

    def test_assistant_factory_method(self):
        """Test assistant message factory method."""
        msg = ChatMessage.assistant("Hi! How can I help?", model="qwen2.5")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi! How can I help?"
        assert msg.metadata == {"model": "qwen2.5"}

    def test_system_factory_method(self):
        """Test system message factory method."""
        msg = ChatMessage.system("You are a helpful assistant.")
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant."

    def test_chat_message_with_metadata(self):
        """Test chat message with custom metadata."""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Test",
            metadata={"key": "value", "count": 42},
        )
        assert msg.metadata["key"] == "value"
        assert msg.metadata["count"] == 42


class TestToolCall:
    """Tests for ToolCall model."""

    def test_create_tool_call(self):
        """Test creating a tool call record."""
        tool_call = ToolCall(
            tool_name="list_tables",
            arguments={"schema": "dbo"},
            result=["Users", "Orders"],
        )
        assert tool_call.tool_name == "list_tables"
        assert tool_call.arguments == {"schema": "dbo"}
        assert tool_call.result == ["Users", "Orders"]
        assert tool_call.success is True
        assert tool_call.error is None

    def test_failed_tool_call(self):
        """Test recording a failed tool call."""
        tool_call = ToolCall(
            tool_name="read_data",
            arguments={"table": "NonExistent"},
            success=False,
            error="Table not found",
        )
        assert tool_call.success is False
        assert tool_call.error == "Table not found"


class TestConversationTurn:
    """Tests for ConversationTurn model."""

    def test_create_conversation_turn(self):
        """Test creating a conversation turn."""
        user_msg = ChatMessage.user("What tables exist?")
        assistant_msg = ChatMessage.assistant("I found Users and Orders tables.")

        turn = ConversationTurn(
            user_message=user_msg,
            assistant_message=assistant_msg,
            duration_ms=150.5,
        )

        assert turn.user_message.content == "What tables exist?"
        assert turn.assistant_message.content == "I found Users and Orders tables."
        assert turn.duration_ms == 150.5
        assert turn.has_tool_calls is False

    def test_turn_with_tool_calls(self):
        """Test conversation turn with tool calls."""
        user_msg = ChatMessage.user("List tables")
        assistant_msg = ChatMessage.assistant("Found 2 tables.")
        tool_calls = [
            ToolCall(tool_name="list_tables", result=["Users", "Orders"]),
        ]

        turn = ConversationTurn(
            user_message=user_msg,
            assistant_message=assistant_msg,
            tool_calls=tool_calls,
        )

        assert turn.has_tool_calls is True
        assert len(turn.tool_calls) == 1
        assert turn.tool_calls[0].tool_name == "list_tables"


class TestConversation:
    """Tests for Conversation model."""

    def test_create_conversation(self):
        """Test creating an empty conversation."""
        conv = Conversation()
        assert conv.total_turns == 0
        assert conv.total_tool_calls == 0
        assert isinstance(conv.created_at, datetime)

    def test_add_turn(self):
        """Test adding turns to conversation."""
        conv = Conversation()

        turn1 = ConversationTurn(
            user_message=ChatMessage.user("Hello"),
            assistant_message=ChatMessage.assistant("Hi!"),
        )
        conv.add_turn(turn1)

        assert conv.total_turns == 1

        turn2 = ConversationTurn(
            user_message=ChatMessage.user("Goodbye"),
            assistant_message=ChatMessage.assistant("Bye!"),
        )
        conv.add_turn(turn2)

        assert conv.total_turns == 2

    def test_get_messages(self):
        """Test getting all messages from conversation."""
        conv = Conversation()

        turn = ConversationTurn(
            user_message=ChatMessage.user("Q1"),
            assistant_message=ChatMessage.assistant("A1"),
        )
        conv.add_turn(turn)

        messages = conv.get_messages()
        assert len(messages) == 2
        assert messages[0].content == "Q1"
        assert messages[1].content == "A1"

    def test_get_history_for_context(self):
        """Test getting history formatted for agent context."""
        conv = Conversation()

        for i in range(5):
            turn = ConversationTurn(
                user_message=ChatMessage.user(f"Q{i}"),
                assistant_message=ChatMessage.assistant(f"A{i}"),
            )
            conv.add_turn(turn)

        # Get all history
        history = conv.get_history_for_context(max_turns=10)
        assert len(history) == 10  # 5 turns * 2 messages

        # Get limited history
        limited = conv.get_history_for_context(max_turns=2)
        assert len(limited) == 4  # 2 turns * 2 messages
        assert limited[0]["content"] == "Q3"  # Most recent 2 turns

    def test_total_tool_calls(self):
        """Test counting total tool calls across turns."""
        conv = Conversation()

        turn1 = ConversationTurn(
            user_message=ChatMessage.user("Q1"),
            assistant_message=ChatMessage.assistant("A1"),
            tool_calls=[
                ToolCall(tool_name="tool1"),
                ToolCall(tool_name="tool2"),
            ],
        )
        turn2 = ConversationTurn(
            user_message=ChatMessage.user("Q2"),
            assistant_message=ChatMessage.assistant("A2"),
            tool_calls=[ToolCall(tool_name="tool3")],
        )

        conv.add_turn(turn1)
        conv.add_turn(turn2)

        assert conv.total_tool_calls == 3

    def test_total_duration_ms(self):
        """Test calculating total duration across turns."""
        conv = Conversation()

        turn1 = ConversationTurn(
            user_message=ChatMessage.user("Q1"),
            assistant_message=ChatMessage.assistant("A1"),
            duration_ms=100.5,
        )
        turn2 = ConversationTurn(
            user_message=ChatMessage.user("Q2"),
            assistant_message=ChatMessage.assistant("A2"),
            duration_ms=200.3,
        )

        conv.add_turn(turn1)
        conv.add_turn(turn2)

        assert conv.total_duration_ms == 300.8

    def test_total_duration_ms_empty(self):
        """Test total duration with no turns."""
        conv = Conversation()
        assert conv.total_duration_ms == 0.0


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_successful_response(self):
        """Test successful agent response."""
        response = AgentResponse(
            content="Here are the results.",
            model="qwen2.5:7b-instruct",
            duration_ms=250.0,
        )

        assert response.content == "Here are the results."
        assert response.success is True
        assert response.model == "qwen2.5:7b-instruct"

    def test_error_response(self):
        """Test error agent response."""
        response = AgentResponse(
            content="",
            error="Connection timeout",
        )

        assert response.success is False
        assert response.error == "Connection timeout"


class TestColumnInfo:
    """Tests for ColumnInfo model."""

    def test_create_column_info(self):
        """Test creating column info."""
        col = ColumnInfo(
            name="UserId",
            data_type="int",
            nullable=False,
            is_primary_key=True,
        )

        assert col.name == "UserId"
        assert col.data_type == "int"
        assert col.nullable is False
        assert col.is_primary_key is True

    def test_column_with_all_fields(self):
        """Test column with all optional fields."""
        col = ColumnInfo(
            name="Email",
            data_type="nvarchar",
            nullable=True,
            is_foreign_key=False,
            default_value="NULL",
            max_length=255,
            description="User email address",
        )

        assert col.max_length == 255
        assert col.description == "User email address"


class TestTableInfo:
    """Tests for TableInfo model."""

    def test_create_table_info(self):
        """Test creating table info."""
        columns = [
            ColumnInfo(name="Id", data_type="int", is_primary_key=True),
            ColumnInfo(name="Name", data_type="nvarchar"),
        ]

        table = TableInfo(
            name="Users",
            schema_name="dbo",
            columns=columns,
            row_count=100,
        )

        assert table.name == "Users"
        assert table.full_name == "dbo.Users"
        assert table.column_names == ["Id", "Name"]
        assert table.primary_key_columns == ["Id"]

    def test_table_info_defaults(self):
        """Test table info default values."""
        table = TableInfo(name="Test")
        assert table.schema_name == "dbo"
        assert table.columns == []


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_create_query_result(self):
        """Test creating query result."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        result = QueryResult(
            rows=rows,
            columns=["id", "name"],
            row_count=2,
            query="SELECT * FROM Users",
        )

        assert result.row_count == 2
        assert result.success is True
        assert result.is_empty is False

    def test_from_rows_factory(self):
        """Test creating result from rows."""
        rows = [
            {"col1": "a", "col2": "b"},
            {"col1": "c", "col2": "d"},
        ]

        result = QueryResult.from_rows(rows, query="SELECT col1, col2 FROM test")

        assert result.columns == ["col1", "col2"]
        assert result.row_count == 2
        assert result.query == "SELECT col1, col2 FROM test"

    def test_from_rows_empty(self):
        """Test from_rows with empty list."""
        result = QueryResult.from_rows([])
        assert result.columns == []
        assert result.row_count == 0
        assert result.is_empty is True

    def test_error_result_factory(self):
        """Test creating error result."""
        result = QueryResult.error_result("Syntax error", query="SELECT *")

        assert result.success is False
        assert result.error == "Syntax error"
        assert result.query == "SELECT *"

    def test_to_markdown_table(self):
        """Test markdown table output."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = QueryResult.from_rows(rows)

        markdown = result.to_markdown_table()

        assert "| id | name |" in markdown
        assert "| --- | --- |" in markdown
        assert "| 1 | Alice |" in markdown
        assert "| 2 | Bob |" in markdown

    def test_to_markdown_table_empty(self):
        """Test markdown table with no results."""
        result = QueryResult()
        assert result.to_markdown_table() == "*No results*"

    def test_to_markdown_table_truncation(self):
        """Test markdown table truncates long results."""
        rows = [{"id": i, "name": f"User{i}"} for i in range(50)]
        result = QueryResult.from_rows(rows)

        markdown = result.to_markdown_table(max_rows=10)

        assert "Showing 10 of 50 rows" in markdown

    def test_to_markdown_table_long_values(self):
        """Test markdown table truncates long values."""
        long_value = "x" * 100
        rows = [{"data": long_value}]
        result = QueryResult.from_rows(rows)

        markdown = result.to_markdown_table()

        # Should be truncated to 50 chars + "..."
        assert "x" * 50 + "..." in markdown


class TestDatabaseSchema:
    """Tests for DatabaseSchema model."""

    def test_create_database_schema(self):
        """Test creating database schema."""
        tables = [
            TableInfo(name="Users"),
            TableInfo(name="Orders"),
        ]

        schema = DatabaseSchema(
            tables=tables,
            database_name="TestDB",
            server_name="localhost",
        )

        assert schema.table_count == 2
        assert schema.table_names == ["Users", "Orders"]
        assert schema.database_name == "TestDB"

    def test_get_table(self):
        """Test getting table by name."""
        tables = [
            TableInfo(name="Users"),
            TableInfo(name="Orders"),
        ]
        schema = DatabaseSchema(tables=tables)

        users_table = schema.get_table("Users")
        assert users_table is not None
        assert users_table.name == "Users"

        # Case insensitive
        orders_table = schema.get_table("ORDERS")
        assert orders_table is not None
        assert orders_table.name == "Orders"

        # Not found
        missing = schema.get_table("NonExistent")
        assert missing is None
