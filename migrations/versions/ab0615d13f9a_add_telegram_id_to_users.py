"""add_telegram_id_to_users

Revision ID: ab0615d13f9a
Revises: 8297c2429e1d
Create Date: 2026-05-17 19:53:07.286177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab0615d13f9a'
down_revision: Union[str, None] = '8297c2429e1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'telegram_id')
