"""add_hospitals

Revision ID: c8921a6eee2f
Revises: caf220bea201
Create Date: 2026-06-05 12:55:43.078692

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8921a6eee2f'
down_revision: str | Sequence[str] | None = 'caf220bea201'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: create hospitals table."""
    op.create_table(
        'hospitals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(254), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('specialties', sa.Text(), nullable=True),
        sa.Column('has_financial_assistance', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hospitals_name', 'hospitals', ['name'])
    op.create_index('ix_hospitals_city', 'hospitals', ['city'])


def downgrade() -> None:
    """Downgrade schema: drop hospitals table."""
    op.drop_index('ix_hospitals_city', table_name='hospitals')
    op.drop_index('ix_hospitals_name', table_name='hospitals')
    op.drop_table('hospitals')
