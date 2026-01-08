"""add_account_lockout_fields

Revision ID: a42a71aaaead
Revises: cc0879b502ec
Create Date: 2026-01-02 23:46:39.672623+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a42a71aaaead"
down_revision: str | None = "cc0879b502ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add account lockout columns to users table
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("last_failed_login_at", sa.DateTime(), nullable=True))

    # Set default for existing rows
    op.execute("UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")


def downgrade() -> None:
    op.drop_column("users", "last_failed_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
