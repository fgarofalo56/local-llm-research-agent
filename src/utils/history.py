"""
Query History Persistence

Provides functionality to persist and recall conversation sessions
using JSON file storage. Enables users to review and continue
previous conversations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.models.chat import ChatMessage, Conversation, ConversationTurn
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default history directory
DEFAULT_HISTORY_DIR = Path.home() / ".local-llm-agent" / "history"


class SessionMetadata(BaseModel):
    """Metadata for a conversation session."""

    session_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str = "Untitled Session"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    turn_count: int = 0
    total_duration_ms: float = 0
    provider: str = ""
    model: str = ""
    tags: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": self.turn_count,
            "total_duration_ms": self.total_duration_ms,
            "provider": self.provider,
            "model": self.model,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionMetadata":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", str(uuid4())[:8]),
            title=data.get("title", "Untitled Session"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            turn_count=data.get("turn_count", 0),
            total_duration_ms=data.get("total_duration_ms", 0),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            tags=data.get("tags", []),
        )


class SessionData(BaseModel):
    """Complete session data including metadata and conversation."""

    metadata: SessionMetadata
    turns: list[dict] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "turns": self.turns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        """Create from dictionary."""
        return cls(
            metadata=SessionMetadata.from_dict(data.get("metadata", {})),
            turns=data.get("turns", []),
        )

    def to_conversation(self) -> Conversation:
        """Convert session data to Conversation object."""
        conversation = Conversation()
        for turn_data in self.turns:
            turn = ConversationTurn(
                user_message=ChatMessage(
                    role="user",
                    content=turn_data["user_message"],
                    timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                ),
                assistant_message=ChatMessage(
                    role="assistant",
                    content=turn_data["assistant_message"],
                    timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                ),
                duration_ms=turn_data.get("duration_ms", 0),
            )
            conversation.add_turn(turn)
        return conversation


class HistoryManager:
    """
    Manages conversation history persistence.

    Stores sessions as JSON files in a configurable directory.
    Supports listing, loading, saving, and deleting sessions.

    Usage:
        history = HistoryManager()

        # Save current conversation
        session_id = history.save_session(conversation, provider="ollama", model="qwen2.5")

        # List all sessions
        sessions = history.list_sessions()

        # Load a session
        session = history.load_session(session_id)

        # Delete a session
        history.delete_session(session_id)
    """

    def __init__(self, history_dir: str | Path | None = None):
        """
        Initialize the history manager.

        Args:
            history_dir: Directory to store history files (default: ~/.local-llm-agent/history)
        """
        self.history_dir = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the history directory exists."""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("history_dir_ensured", path=str(self.history_dir))

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.history_dir / f"{session_id}.json"

    def _generate_title(self, conversation: Conversation) -> str:
        """Generate a title from the first user message."""
        if conversation.turns:
            first_message = conversation.turns[0].user_message.content
            # Truncate to first 50 characters
            if len(first_message) > 50:
                return first_message[:47] + "..."
            return first_message
        return "Empty Session"

    def save_session(
        self,
        conversation: Conversation,
        session_id: str | None = None,
        title: str | None = None,
        provider: str = "",
        model: str = "",
        tags: list[str] | None = None,
    ) -> str:
        """
        Save a conversation session.

        Args:
            conversation: Conversation to save
            session_id: Optional session ID (generates new if not provided)
            title: Optional title (auto-generated if not provided)
            provider: LLM provider name
            model: Model name
            tags: Optional tags for categorization

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid4())[:8]

        # Build turn data
        turns = [
            {
                "user_message": turn.user_message.content,
                "assistant_message": turn.assistant_message.content,
                "timestamp": turn.user_message.timestamp.isoformat(),
                "duration_ms": turn.duration_ms,
            }
            for turn in conversation.turns
        ]

        # Build metadata
        metadata = SessionMetadata(
            session_id=session_id,
            title=title or self._generate_title(conversation),
            updated_at=datetime.now(),
            turn_count=conversation.total_turns,
            total_duration_ms=conversation.total_duration_ms,
            provider=provider,
            model=model,
            tags=tags or [],
        )

        # Check if updating existing session
        existing_path = self._get_session_path(session_id)
        if existing_path.exists():
            try:
                existing_data = json.loads(existing_path.read_text(encoding="utf-8"))
                metadata.created_at = datetime.fromisoformat(
                    existing_data.get("metadata", {}).get("created_at", datetime.now().isoformat())
                )
            except Exception:
                pass

        # Build session data
        session = SessionData(metadata=metadata, turns=turns)

        # Save to file
        filepath = self._get_session_path(session_id)
        filepath.write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("session_saved", session_id=session_id, turns=len(turns))
        return session_id

    def load_session(self, session_id: str) -> SessionData | None:
        """
        Load a session by ID.

        Args:
            session_id: Session ID to load

        Returns:
            SessionData or None if not found
        """
        filepath = self._get_session_path(session_id)
        if not filepath.exists():
            logger.warning("session_not_found", session_id=session_id)
            return None

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            session = SessionData.from_dict(data)
            logger.info("session_loaded", session_id=session_id)
            return session
        except Exception as e:
            logger.error("session_load_error", session_id=session_id, error=str(e))
            return None

    def list_sessions(
        self,
        limit: int | None = None,
        tags: list[str] | None = None,
    ) -> list[SessionMetadata]:
        """
        List all available sessions.

        Args:
            limit: Maximum number of sessions to return
            tags: Filter by tags (any match)

        Returns:
            List of session metadata, sorted by updated_at descending
        """
        sessions = []

        for filepath in self.history_dir.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                metadata = SessionMetadata.from_dict(data.get("metadata", {}))

                # Filter by tags if specified
                if tags:
                    if not any(tag in metadata.tags for tag in tags):
                        continue

                sessions.append(metadata)
            except Exception as e:
                logger.warning("session_list_error", filepath=str(filepath), error=str(e))

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        if limit:
            sessions = sessions[:limit]

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        filepath = self._get_session_path(session_id)
        if filepath.exists():
            filepath.unlink()
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    def clear_all(self) -> int:
        """
        Delete all sessions.

        Returns:
            Number of sessions deleted
        """
        count = 0
        for filepath in self.history_dir.glob("*.json"):
            filepath.unlink()
            count += 1

        logger.info("all_sessions_cleared", count=count)
        return count

    def search_sessions(self, query: str, limit: int = 10) -> list[SessionMetadata]:
        """
        Search sessions by title or content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching session metadata
        """
        query_lower = query.lower()
        results = []

        for filepath in self.history_dir.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                metadata = SessionMetadata.from_dict(data.get("metadata", {}))

                # Search in title
                if query_lower in metadata.title.lower():
                    results.append(metadata)
                    continue

                # Search in turn content
                for turn in data.get("turns", []):
                    if query_lower in turn.get("user_message", "").lower():
                        results.append(metadata)
                        break
                    if query_lower in turn.get("assistant_message", "").lower():
                        results.append(metadata)
                        break

            except Exception:
                continue

        # Sort by relevance (title match first) and then by date
        results.sort(key=lambda s: (query_lower in s.title.lower(), s.updated_at), reverse=True)

        return results[:limit]


# Singleton instance
_history_manager: HistoryManager | None = None


def get_history_manager(history_dir: str | Path | None = None) -> HistoryManager:
    """
    Get or create the singleton history manager.

    Args:
        history_dir: Optional custom history directory

    Returns:
        HistoryManager instance
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager(history_dir)
    return _history_manager


def reset_history_manager() -> None:
    """Reset the singleton history manager."""
    global _history_manager
    _history_manager = None
