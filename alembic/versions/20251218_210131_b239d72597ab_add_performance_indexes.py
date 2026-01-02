"""add_performance_indexes

Revision ID: b239d72597ab
Revises: add_tags_to_documents
Create Date: 2025-12-18 21:01:31.517681+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b239d72597ab'
down_revision: Union[str, None] = 'add_tags_to_documents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes to frequently queried columns."""
    # Conversations indexes
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('ix_conversations_is_archived', 'conversations', ['is_archived'])

    # Messages indexes
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])

    # Documents indexes
    op.create_index('ix_documents_processing_status', 'documents', ['processing_status'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])

    # Query history indexes
    op.create_index('ix_query_history_is_favorite', 'query_history', ['is_favorite'])
    op.create_index('ix_query_history_created_at', 'query_history', ['created_at'])
    op.create_index('ix_query_history_conversation_id', 'query_history', ['conversation_id'])

    # Dashboards indexes
    op.create_index('ix_dashboards_created_at', 'dashboards', ['created_at'])
    op.create_index('ix_dashboards_is_default', 'dashboards', ['is_default'])

    # Dashboard widgets indexes
    op.create_index('ix_dashboard_widgets_dashboard_id', 'dashboard_widgets', ['dashboard_id'])
    op.create_index('ix_dashboard_widgets_widget_type', 'dashboard_widgets', ['widget_type'])

    # Data alerts indexes
    op.create_index('ix_data_alerts_is_active', 'data_alerts', ['is_active'])
    op.create_index('ix_data_alerts_last_checked_at', 'data_alerts', ['last_checked_at'])

    # MCP server configs indexes
    op.create_index('ix_mcp_server_configs_is_enabled', 'mcp_server_configs', ['is_enabled'])

    # Scheduled queries indexes
    op.create_index('ix_scheduled_queries_is_active', 'scheduled_queries', ['is_active'])
    op.create_index('ix_scheduled_queries_next_run_at', 'scheduled_queries', ['next_run_at'])

    # Theme configs indexes
    op.create_index('ix_theme_configs_is_active', 'theme_configs', ['is_active'])


def downgrade() -> None:
    """Remove performance indexes."""
    # Theme configs indexes
    op.drop_index('ix_theme_configs_is_active', table_name='theme_configs')

    # Scheduled queries indexes
    op.drop_index('ix_scheduled_queries_next_run_at', table_name='scheduled_queries')
    op.drop_index('ix_scheduled_queries_is_active', table_name='scheduled_queries')

    # MCP server configs indexes
    op.drop_index('ix_mcp_server_configs_is_enabled', table_name='mcp_server_configs')

    # Data alerts indexes
    op.drop_index('ix_data_alerts_last_checked_at', table_name='data_alerts')
    op.drop_index('ix_data_alerts_is_active', table_name='data_alerts')

    # Dashboard widgets indexes
    op.drop_index('ix_dashboard_widgets_widget_type', table_name='dashboard_widgets')
    op.drop_index('ix_dashboard_widgets_dashboard_id', table_name='dashboard_widgets')

    # Dashboards indexes
    op.drop_index('ix_dashboards_is_default', table_name='dashboards')
    op.drop_index('ix_dashboards_created_at', table_name='dashboards')

    # Query history indexes
    op.drop_index('ix_query_history_conversation_id', table_name='query_history')
    op.drop_index('ix_query_history_created_at', table_name='query_history')
    op.drop_index('ix_query_history_is_favorite', table_name='query_history')

    # Documents indexes
    op.drop_index('ix_documents_created_at', table_name='documents')
    op.drop_index('ix_documents_processing_status', table_name='documents')

    # Messages indexes
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')

    # Conversations indexes
    op.drop_index('ix_conversations_is_archived', table_name='conversations')
    op.drop_index('ix_conversations_created_at', table_name='conversations')
