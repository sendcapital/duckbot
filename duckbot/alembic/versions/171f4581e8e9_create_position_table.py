"""create_position_table

Revision ID: 171f4581e8e9
Revises: 1dc3ce004a6e
Create Date: 2024-09-21 15:38:03.019316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, Index, BigInteger, ForeignKey, PrimaryKeyConstraint, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision: str = '171f4581e8e9'
down_revision: Union[str, None] = '1dc3ce004a6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'positions',
        sa.Column('telegram_user_id', sa.BigInteger, sa.ForeignKey('users.telegram_user_id'), nullable=False),
        sa.Column('market_id', sa.Integer, sa.ForeignKey('markets.market_id'), nullable=False),
        sa.Column('size', sa.Integer, nullable=False),
        sa.Column('notional', sa.Integer, nullable=False),
        sa.Column('prediction', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.PrimaryKeyConstraint('telegram_user_id', 'market_id')
    )


def downgrade() -> None:
    op.drop_table('positions')
