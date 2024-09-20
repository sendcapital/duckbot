"""Initial migration

Revision ID: 7937534aa760
Revises: 
Create Date: 2024-09-20 22:52:00.787113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7937534aa760'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
    sa.Column('telegram_username', sa.String(), nullable=False),
    sa.Column('language_code', sa.String(), nullable=True),
    sa.Column('bot', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('telegram_user_id')
    )
    op.create_index('index_users_on_telegram_user_id', 'users', ['telegram_user_id'], unique=False)
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('index_users_on_telegram_user_id', table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
