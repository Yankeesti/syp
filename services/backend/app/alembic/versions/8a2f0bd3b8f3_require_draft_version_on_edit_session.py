"""Require draft version on edit sessions.

Revision ID: 8a2f0bd3b8f3
Revises: 4ee3041509b5
Create Date: 2026-01-31 18:02:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8a2f0bd3b8f3"
down_revision: Union[str, Sequence[str], None] = "4ee3041509b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    fk_name = None
    for fk in inspector.get_foreign_keys("quiz_edit_session"):
        if fk.get("constrained_columns") == ["draft_version_id"]:
            fk_name = fk.get("name")
            break

    if fk_name:
        op.drop_constraint(fk_name, "quiz_edit_session", type_="foreignkey")

    op.execute("DELETE FROM quiz_edit_session WHERE draft_version_id IS NULL")
    op.alter_column(
        "quiz_edit_session",
        "draft_version_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_quiz_edit_session_draft_version_id",
        "quiz_edit_session",
        "quiz_version",
        ["draft_version_id"],
        ["quiz_version_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_quiz_edit_session_draft_version_id",
        "quiz_edit_session",
        type_="foreignkey",
    )
    op.alter_column(
        "quiz_edit_session",
        "draft_version_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_quiz_edit_session_draft_version_id",
        "quiz_edit_session",
        "quiz_version",
        ["draft_version_id"],
        ["quiz_version_id"],
        ondelete="SET NULL",
    )
