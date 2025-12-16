"""
Chat Message Models

Pydantic models for representing chat messages, conversations,
and agent interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def user(cls, content: str, **metadata: Any) -> "ChatMessage":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content, metadata=metadata)

    @classmethod
    def assistant(cls, content: str, **metadata: Any) -> "ChatMessage":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content, metadata=metadata)

    @classmethod
    def system(cls, content: str, **metadata: Any) -> "ChatMessage":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content, metadata=metadata)


class ToolCall(BaseModel):
    """Record of a tool call made by the agent."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationTurn(BaseModel):
    """A single turn in a conversation (user input + agent response)."""

    user_message: ChatMessage
    assistant_message: ChatMessage
    tool_calls: list[ToolCall] = Field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def has_tool_calls(self) -> bool:
        """Check if this turn involved tool calls."""
        return len(self.tool_calls) > 0


class Conversation(BaseModel):
    """A complete conversation with history."""

    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    turns: list[ConversationTurn] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a turn to the conversation."""
        self.turns.append(turn)

    def get_messages(self) -> list[ChatMessage]:
        """Get all messages in chronological order."""
        messages = []
        for turn in self.turns:
            messages.append(turn.user_message)
            messages.append(turn.assistant_message)
        return messages

    def get_history_for_context(self, max_turns: int = 10) -> list[dict[str, str]]:
        """
        Get conversation history formatted for agent context.

        Args:
            max_turns: Maximum number of turns to include

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        recent_turns = self.turns[-max_turns:] if max_turns else self.turns
        history = []
        for turn in recent_turns:
            history.append({"role": "user", "content": turn.user_message.content})
            history.append({"role": "assistant", "content": turn.assistant_message.content})
        return history

    @property
    def total_turns(self) -> int:
        """Get total number of turns."""
        return len(self.turns)

    @property
    def total_tool_calls(self) -> int:
        """Get total number of tool calls across all turns."""
        return sum(len(turn.tool_calls) for turn in self.turns)

    @property
    def total_duration_ms(self) -> float:
        """Get total duration across all turns in milliseconds."""
        return sum(turn.duration_ms for turn in self.turns)


class TokenUsage(BaseModel):
    """Token usage statistics for a response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_pydantic_usage(cls, usage: Any) -> "TokenUsage":
        """Create TokenUsage from Pydantic AI Usage object."""
        if usage is None:
            return cls()
        return cls(
            prompt_tokens=getattr(usage, "request_tokens", 0) or 0,
            completion_tokens=getattr(usage, "response_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
        )

    def __str__(self) -> str:
        """Format token usage as a string."""
        return f"{self.prompt_tokens:,} in / {self.completion_tokens:,} out / {self.total_tokens:,} total"


class AgentResponse(BaseModel):
    """Response from the research agent."""

    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    duration_ms: float = 0.0
    model: str = ""
    error: str | None = None
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    @property
    def success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None
