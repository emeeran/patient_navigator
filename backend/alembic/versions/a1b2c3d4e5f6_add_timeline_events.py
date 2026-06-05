"""add_timeline_events

Revision ID: a1b2c3d4e5f6
Revises: 6a563b58a60d
Create Date: 2026-06-04 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '6a563b58a60d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timeline_events table for case lifecycle tracking."""
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('case_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('old_value', sa.String(length=500), nullable=True),
        sa.Column('new_value', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_timeline_case', 'timeline_events', ['case_id'], unique=False)
    op.create_index('idx_timeline_case_created', 'timeline_events', ['case_id', 'created_at'], unique=False)
    op.create_index('idx_timeline_event_type', 'timeline_events', ['event_type'], unique=False)

    # INSERT-only enforcement (same pattern as audit_log)
    op.execute("""
        CREATE RULE timeline_events_no_update AS
            ON UPDATE TO timeline_events DO INSTEAD NOTHING;
    """)
    op.execute("""
        CREATE RULE timeline_events_no_delete AS
            ON DELETE TO timeline_events DO INSTEAD NOTHING;
    """)


def downgrade() -> None:
    """Remove timeline_events table."""
    op.execute("DROP RULE IF EXISTS timeline_events_no_delete ON timeline_events")
    op.execute("DROP RULE IF EXISTS timeline_events_no_update ON timeline_events")
    op.drop_index('idx_timeline_event_type', table_name='timeline_events')
    op.drop_index('idx_timeline_case_created', table_name='timeline_events')
    op.drop_index('idx_timeline_case', table_name='timeline_events')
    op.drop_table('timeline_events')
