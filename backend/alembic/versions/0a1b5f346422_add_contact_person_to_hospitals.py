"""add contact_person to hospitals

Revision ID: 0a1b5f346422
Revises: 741913336db1
Create Date: 2026-06-07 22:15:07.417365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0a1b5f346422'
down_revision: Union[str, Sequence[str], None] = '741913336db1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('contact_person', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('hospitals', 'contact_person')
