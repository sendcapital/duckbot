"""add_market_name_to_market_table

Revision ID: 1aef71d0d1ec
Revises: 171f4581e8e9
Create Date: 2024-09-21 16:12:32.322167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1aef71d0d1ec'
down_revision: Union[str, None] = '171f4581e8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('markets', sa.Column('market_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('markets', 'market_name')
