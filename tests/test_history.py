"""
Tests for Query History Persistence

Tests the history persistence functionality for conversation sessions.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.models.chat import ChatMessage, Conversation, ConversationTurn
from src.utils.history import (
    HistoryManager,
    SessionData,
    SessionMetadata,
    get_history_manager,
    reset_history_manager,
)


@pytest.fixture
def temp_history_dir():
    """Create a temporary history directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def history_manager(temp_history_dir):
    """Create a history manager with temporary directory."""
    return HistoryManager(temp_history_dir)


@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    conv = Conversation()
    turn1 = ConversationTurn(
        user_message=ChatMessage.user("Hello, what tables are available?"),
        assistant_message=ChatMessage.assistant("There are 5 tables in the database."),
        duration_ms=100,
    )
    turn2 = ConversationTurn(
        user_message=ChatMessage.user("Show me the users table"),
        assistant_message=ChatMessage.assistant("The users table has columns: id, name, email."),
        duration_ms=150,
    )
    conv.add_turn(turn1)
    conv.add_turn(turn2)
    return conv


class TestSessionMetadata:
    """Tests for SessionMetadata class."""

    def test_create_metadata(self):
        """Test creating session metadata."""
        metadata = SessionMetadata(
            title="Test Session",
            provider="ollama",
            model="qwen2.5",
        )
        assert metadata.title == "Test Session"
        assert metadata.provider == "ollama"
        assert metadata.model == "qwen2.5"
        assert len(metadata.session_id) == 8

    def test_to_dict(self):
        """Test converting metadata to dict."""
        metadata = SessionMetadata(
            session_id="test123",
            title="Test",
            turn_count=5,
        )
        data = metadata.to_dict()

        assert data["session_id"] == "test123"
        assert data["title"] == "Test"
        assert data["turn_count"] == 5
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test creating metadata from dict."""
        data = {
            "session_id": "abc12345",
            "title": "Restored Session",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T13:00:00",
            "turn_count": 10,
            "provider": "foundry_local",
            "model": "phi-4",
            "tags": ["test", "demo"],
        }
        metadata = SessionMetadata.from_dict(data)

        assert metadata.session_id == "abc12345"
        assert metadata.title == "Restored Session"
        assert metadata.turn_count == 10
        assert metadata.provider == "foundry_local"
        assert metadata.tags == ["test", "demo"]


class TestSessionData:
    """Tests for SessionData class."""

    def test_to_conversation(self, sample_conversation):
        """Test converting session data to conversation."""
        turns = [
            {
                "user_message": "Hello",
                "assistant_message": "Hi there!",
                "timestamp": datetime.now().isoformat(),
                "duration_ms": 100,
            },
        ]
        session = SessionData(
            metadata=SessionMetadata(title="Test"),
            turns=turns,
        )
        conv = session.to_conversation()

        assert conv.total_turns == 1
        assert conv.turns[0].user_message.content == "Hello"
        assert conv.turns[0].assistant_message.content == "Hi there!"


class TestHistoryManager:
    """Tests for HistoryManager class."""

    def test_save_and_load_session(self, history_manager, sample_conversation):
        """Test saving and loading a session."""
        session_id = history_manager.save_session(
            sample_conversation,
            title="Test Session",
            provider="ollama",
            model="qwen2.5",
        )

        assert len(session_id) == 8

        # Load the session
        loaded = history_manager.load_session(session_id)
        assert loaded is not None
        assert loaded.metadata.title == "Test Session"
        assert loaded.metadata.provider == "ollama"
        assert loaded.metadata.model == "qwen2.5"
        assert loaded.metadata.turn_count == 2
        assert len(loaded.turns) == 2

    def test_auto_generate_title(self, history_manager, sample_conversation):
        """Test auto-generating title from first message."""
        session_id = history_manager.save_session(sample_conversation)

        loaded = history_manager.load_session(session_id)
        assert loaded is not None
        assert "Hello" in loaded.metadata.title

    def test_list_sessions(self, history_manager, sample_conversation):
        """Test listing sessions."""
        # Save multiple sessions
        history_manager.save_session(sample_conversation, title="Session 1")
        history_manager.save_session(sample_conversation, title="Session 2")
        history_manager.save_session(sample_conversation, title="Session 3")

        sessions = history_manager.list_sessions()
        assert len(sessions) == 3

        # Test limit
        sessions = history_manager.list_sessions(limit=2)
        assert len(sessions) == 2

    def test_list_sessions_sorted_by_date(self, history_manager, sample_conversation):
        """Test that sessions are sorted by updated_at descending."""
        history_manager.save_session(sample_conversation, title="First")
        history_manager.save_session(sample_conversation, title="Second")
        history_manager.save_session(sample_conversation, title="Third")

        sessions = history_manager.list_sessions()
        # Most recent should be first
        assert sessions[0].title == "Third"

    def test_delete_session(self, history_manager, sample_conversation):
        """Test deleting a session."""
        session_id = history_manager.save_session(sample_conversation, title="To Delete")

        assert history_manager.delete_session(session_id) is True
        assert history_manager.load_session(session_id) is None

        # Deleting non-existent session
        assert history_manager.delete_session("nonexistent") is False

    def test_clear_all(self, history_manager, sample_conversation):
        """Test clearing all sessions."""
        history_manager.save_session(sample_conversation, title="Session 1")
        history_manager.save_session(sample_conversation, title="Session 2")

        count = history_manager.clear_all()
        assert count == 2
        assert len(history_manager.list_sessions()) == 0

    def test_search_sessions(self, history_manager, sample_conversation):
        """Test searching sessions."""
        # Clear any existing sessions first (test isolation)
        history_manager.clear_all()

        history_manager.save_session(sample_conversation, title="Weather forecast")
        history_manager.save_session(sample_conversation, title="User management")
        history_manager.save_session(sample_conversation, title="Table analysis")

        # Search by unique title keyword (only "Weather forecast" matches "weather")
        results = history_manager.search_sessions("weather")
        assert len(results) == 1
        assert results[0].title == "Weather forecast"

        # Search by content (should find "table" in message content)
        results = history_manager.search_sessions("users")
        assert len(results) >= 1

    def test_load_nonexistent_session(self, history_manager):
        """Test loading a session that doesn't exist."""
        result = history_manager.load_session("nonexistent")
        assert result is None

    def test_update_existing_session(self, history_manager, sample_conversation):
        """Test updating an existing session preserves created_at."""
        session_id = history_manager.save_session(
            sample_conversation,
            title="Original",
        )

        # Load and check created_at
        original = history_manager.load_session(session_id)
        original_created = original.metadata.created_at

        # Update the session
        history_manager.save_session(
            sample_conversation,
            session_id=session_id,
            title="Updated",
        )

        # Load again and verify
        updated = history_manager.load_session(session_id)
        assert updated.metadata.title == "Updated"
        assert updated.metadata.created_at == original_created

    def test_filter_by_tags(self, history_manager, sample_conversation):
        """Test filtering sessions by tags."""
        history_manager.save_session(sample_conversation, title="Tagged", tags=["sql", "demo"])
        history_manager.save_session(sample_conversation, title="Untagged")

        # Filter by tag
        results = history_manager.list_sessions(tags=["sql"])
        assert len(results) == 1
        assert results[0].title == "Tagged"


class TestSingletonManager:
    """Tests for singleton history manager."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_history_manager()

    def test_get_singleton(self):
        """Test getting singleton manager."""
        manager1 = get_history_manager()
        manager2 = get_history_manager()
        assert manager1 is manager2

    def test_reset_singleton(self):
        """Test resetting singleton."""
        manager1 = get_history_manager()
        reset_history_manager()
        manager2 = get_history_manager()
        assert manager1 is not manager2
