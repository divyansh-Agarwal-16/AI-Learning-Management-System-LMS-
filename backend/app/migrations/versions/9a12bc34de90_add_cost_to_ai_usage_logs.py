"""add cost to ai_usage_logs

Revision ID: 9a12bc34de90
Revises: 8961ac5de682
Create Date: 2026-06-22 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: sa.String = '9a12bc34de90'
down_revision: Union[str, None] = '8961ac5de682'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cost column to ai_usage_logs table
    op.add_column(
        'ai_usage_logs',
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0')
    )


def downgrade() -> None:
    # Remove cost column from ai_usage_logs table
    op.drop_column('ai_usage_logs', 'cost')
