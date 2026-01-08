"""Add tags column to documents table

Revision ID: add_tags_to_documents
Revises: 7634261e3e9e
Create Date: 2025-12-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_tags_to_documents"
down_revision: str | None = "7634261e3e9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add tags column to documents table."""
    op.add_column(
        "documents",
        sa.Column("tags", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove tags column from documents table."""
    op.drop_column("documents", "tags")
