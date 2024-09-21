"""create_market_table

Revision ID: 1dc3ce004a6e
Revises: 9e8a59dcf5c7
Create Date: 2024-09-21 15:36:33.835400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dc3ce004a6e'
down_revision: Union[str, None] = '9e8a59dcf5c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'markets',
        sa.Column('market_id', sa.Integer, nullable=False),
        sa.Column('book', sa.ARRAY(sa.Integer), nullable=False),
        sa.Column('price_tick', sa.Integer, nullable=False),
        sa.Column('ask_index', sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint('market_id')
    )

def downgrade() -> None:
    op.drop_table('markets')
