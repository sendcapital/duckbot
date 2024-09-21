"""add_market_cols_to_market_table

Revision ID: f6fd326fbf79
Revises: 1aef71d0d1ec
Create Date: 2024-09-21 17:06:05.777140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6fd326fbf79'
down_revision: Union[str, None] = '1aef71d0d1ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('markets', sa.Column('category', sa.String(), nullable=False))
    op.add_column('markets', sa.Column('market_close', sa.Boolean(), nullable=False))
    op.add_column('markets', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('markets', sa.Column('closed_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('markets', 'category')
    op.drop_column('markets', 'closed_at')
    op.drop_column('markets', 'created_at')
    op.drop_column('markets', 'market_close')

