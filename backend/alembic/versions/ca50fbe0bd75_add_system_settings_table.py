"""add_system_settings_table

Revision ID: ca50fbe0bd75
Revises: c8921a6eee2f
Create Date: 2026-06-05 16:39:18.463697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca50fbe0bd75'
down_revision: Union[str, Sequence[str], None] = 'c8921a6eee2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('system_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=10), server_default='str', nullable=False),
        sa.Column('group_name', sa.String(length=50), nullable=False),
        sa.Column('editable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('system_settings')
