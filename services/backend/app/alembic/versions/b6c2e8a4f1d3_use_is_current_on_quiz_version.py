"""Use is_current flag on quiz versions.

Revision ID: b6c2e8a4f1d3
Revises: 8a2f0bd3b8f3
Create Date: 2026-01-31 19:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6c2e8a4f1d3"
down_revision: Union[str, Sequence[str], None] = "8a2f0bd3b8f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "quiz_version",
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Whether this is the current version for the quiz",
        ),
    )

    op.execute(
        """
        UPDATE quiz_version
        SET is_current = true
        FROM quiz
        WHERE quiz.current_version_id = quiz_version.quiz_version_id
        """,
    )

    op.create_index(
        "uq_quiz_version_current",
        "quiz_version",
        ["quiz_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
        sqlite_where=sa.text("is_current = 1"),
    )

    op.drop_constraint("fk_quiz_current_version", "quiz", type_="foreignkey")
    op.drop_column("quiz", "current_version_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "quiz",
        sa.Column(
            "current_version_id",
            sa.Uuid(),
            nullable=True,
            comment="Current published version of this quiz",
        ),
    )

    op.execute(
        """
        UPDATE quiz
        SET current_version_id = quiz_version.quiz_version_id
        FROM quiz_version
        WHERE quiz_version.quiz_id = quiz.quiz_id
          AND quiz_version.is_current = true
        """,
    )

    op.create_foreign_key(
        "fk_quiz_current_version",
        "quiz",
        "quiz_version",
        ["current_version_id"],
        ["quiz_version_id"],
        ondelete="SET NULL",
    )

    op.drop_index("uq_quiz_version_current", table_name="quiz_version")
    op.drop_column("quiz_version", "is_current")
