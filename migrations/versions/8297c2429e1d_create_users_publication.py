"""create_users_publication

Revision ID: 8297c2429e1d
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17 19:15:27.078967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8297c2429e1d'
down_revision: Union[str, None] = '0c4494a74f5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_publication WHERE pubname = 'users_publication'
            ) THEN
                CREATE PUBLICATION users_publication FOR TABLE users;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP PUBLICATION IF EXISTS users_publication")
