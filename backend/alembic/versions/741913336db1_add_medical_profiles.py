"""add_medical_profiles

Revision ID: 741913336db1
Revises: 1884b38009f6
Create Date: 2026-06-06 15:03:45.415872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '741913336db1'
down_revision: Union[str, Sequence[str], None] = '1884b38009f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('medical_profiles',
    sa.Column('patient_id', sa.UUID(), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('height_cm', sa.Float(), nullable=True),
    sa.Column('weight_kg', sa.Float(), nullable=True),
    sa.Column('blood_type', sa.String(length=10), nullable=True),
    sa.Column('past_medical_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('family_medical_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('chronic_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('current_medications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('allergies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('patient_id')
    )
    op.create_index('idx_medical_profiles_patient', 'medical_profiles', ['patient_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_medical_profiles_patient', table_name='medical_profiles')
    op.drop_table('medical_profiles')
