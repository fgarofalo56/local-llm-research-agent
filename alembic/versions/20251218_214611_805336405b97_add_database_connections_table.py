"""add_database_connections_table

Revision ID: 805336405b97
Revises: b239d72597ab
Create Date: 2025-12-18 21:46:11.825336+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '805336405b97'
down_revision: Union[str, None] = 'b239d72597ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'database_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('db_type', sa.String(length=50), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('ssl_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('trust_certificate', sa.Boolean(), nullable=True, default=False),
        sa.Column('additional_options', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('last_test_success', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    op.drop_table('database_connections')
