"""add_documents

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add documents table."""
    op.create_table(
        'documents',
        sa.Column('case_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('stored_filename', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('ocr_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('ocr_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_by', sa.UUID(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_documents_case', 'documents', ['case_id'], unique=False)
    op.create_index('idx_documents_uploaded_by', 'documents', ['uploaded_by'], unique=False)
    op.create_index('idx_documents_ocr_status', 'documents', ['ocr_status'], unique=False)


def downgrade() -> None:
    """Remove documents table."""
    op.drop_index('idx_documents_ocr_status', table_name='documents')
    op.drop_index('idx_documents_uploaded_by', table_name='documents')
    op.drop_index('idx_documents_case', table_name='documents')
    op.drop_table('documents')
