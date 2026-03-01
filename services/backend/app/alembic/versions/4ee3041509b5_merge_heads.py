"""merge heads

Revision ID: 4ee3041509b5
Revises: 8b4c9f7a0e2d, 46599c599156
Create Date: 2026-01-31 17:14:17.802980

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4ee3041509b5"
down_revision: Union[str, Sequence[str], None] = ("8b4c9f7a0e2d", "46599c599156")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
