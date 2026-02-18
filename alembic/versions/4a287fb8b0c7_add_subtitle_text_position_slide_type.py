"""add subtitle text_position slide_type

Revision ID: 4a287fb8b0c7
Revises: e42cd11a2865
Create Date: 2026-02-18 03:39:48.418381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a287fb8b0c7'
down_revision: Union[str, None] = 'e42cd11a2865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('slides', sa.Column('subtitle', sa.String(length=500), server_default='', nullable=False))
    op.add_column('slides', sa.Column('text_position', sa.String(length=20), server_default='none', nullable=False))
    op.add_column('slides', sa.Column('slide_type', sa.String(length=20), server_default='content', nullable=False))


def downgrade() -> None:
    op.drop_column('slides', 'slide_type')
    op.drop_column('slides', 'text_position')
    op.drop_column('slides', 'subtitle')
