"""
Database Models
Phase 2.1: Backend Infrastructure & RAG Pipeline

SQLAlchemy ORM models for all database tables.
Based on alembic migration: 7634261e3e9e_initial_phase2_tables
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Conversation(Base):
    """Conversation model for chat history."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)

    # Relationship
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for conversation messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20))  # 'user', 'assistant', 'system'
    content = Column(Text)
    tool_calls = Column(Text)  # JSON array of tool calls
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


class Dashboard(Base):
    """Dashboard model for user dashboards."""

    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    layout = Column(Text)  # JSON layout configuration
    is_default = Column(Boolean, default=False)
    share_token = Column(String(64), unique=True)
    share_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")


class Widget(Base):
    """Widget model for dashboard widgets."""

    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id", ondelete="CASCADE"))
    widget_type = Column(String(50))  # 'chart', 'kpi', 'table'
    title = Column(String(255))
    query = Column(Text)
    chart_config = Column(Text)  # JSON chart configuration
    position = Column(Text)  # JSON position object {x, y, w, h}
    refresh_interval = Column(Integer)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    dashboard = relationship("Dashboard", back_populates="widgets")


class DataAlert(Base):
    """Data alert model for monitoring queries."""

    __tablename__ = "data_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    query = Column(Text)
    condition = Column(String(50))  # 'greater_than', 'less_than', 'equals', etc.
    threshold = Column(Numeric(18, 4))
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    last_triggered_at = Column(DateTime)
    last_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Document model for uploaded documents."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255))
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    chunk_count = Column(Integer)
    processing_status = Column(String(50))  # 'pending', 'processing', 'completed', 'failed'
    error_message = Column(Text)
    tags = Column(Text)  # JSON array of tags (added in migration add_tags_to_documents)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class MCPServerConfig(Base):
    """MCP Server configuration model."""

    __tablename__ = "mcp_server_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(100), unique=True)
    name = Column(String(255))
    description = Column(Text)
    server_type = Column(String(20))  # 'stdio', 'http'
    command = Column(Text)  # For stdio servers
    args = Column(Text)  # JSON array of command arguments
    url = Column(String(500))  # For HTTP servers
    environment = Column(Text)  # JSON object of environment variables
    is_enabled = Column(Boolean, default=True)
    is_built_in = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedQuery(Base):
    """Saved query model for user-saved SQL queries."""

    __tablename__ = "saved_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    description = Column(Text)
    query = Column(Text)
    tags = Column(Text)  # JSON array of tags
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledQuery(Base):
    """Scheduled query model for automated query execution."""

    __tablename__ = "scheduled_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    query = Column(Text)
    cron_expression = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryHistory(Base):
    """Query history model for tracking executed queries."""

    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"))
    natural_language = Column(Text)
    generated_sql = Column(Text)
    result_row_count = Column(Integer)
    execution_time_ms = Column(Integer)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThemeConfig(Base):
    """Theme configuration model."""

    __tablename__ = "theme_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True)
    display_name = Column(String(255))
    config = Column(Text)  # JSON theme configuration
    is_preset = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
