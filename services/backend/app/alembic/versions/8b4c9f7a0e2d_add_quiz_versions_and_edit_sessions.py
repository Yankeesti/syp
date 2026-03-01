"""add quiz versions and edit sessions

Revision ID: 8b4c9f7a0e2d
Revises: 3f21ababfc70
Create Date: 2026-01-30 12:00:00.000000
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b4c9f7a0e2d"
down_revision: Union[str, Sequence[str], None] = "3f21ababfc70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "quiz_version",
        sa.Column(
            "quiz_version_id",
            sa.Uuid(),
            nullable=False,
            comment="UUID primary key",
        ),
        sa.Column("quiz_id", sa.Uuid(), nullable=False, comment="Foreign key to quiz"),
        sa.Column(
            "base_version_id",
            sa.Uuid(),
            nullable=True,
            comment="Optional base version for drafts",
        ),
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=True,
            comment="Sequential version number (assigned on commit)",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PUBLISHED",
                name="quizversionstatus",
                native_enum=False,
                length=20,
            ),
            nullable=False,
            comment="Version status (draft/published)",
        ),
        sa.Column(
            "created_by",
            sa.Uuid(),
            nullable=False,
            comment="UUID of user who created the version",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timestamp when version was created",
        ),
        sa.Column(
            "committed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when version was committed",
        ),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.quiz_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["base_version_id"],
            ["quiz_version.quiz_version_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("quiz_version_id"),
    )
    op.create_index(
        op.f("ix_quiz_version_quiz_id"),
        "quiz_version",
        ["quiz_id"],
        unique=False,
    )

    op.create_table(
        "quiz_edit_session",
        sa.Column(
            "edit_session_id",
            sa.Uuid(),
            nullable=False,
            comment="UUID primary key",
        ),
        sa.Column("quiz_id", sa.Uuid(), nullable=False, comment="Foreign key to quiz"),
        sa.Column(
            "draft_version_id",
            sa.Uuid(),
            nullable=True,
            comment="Draft version associated with this session",
        ),
        sa.Column(
            "started_by",
            sa.Uuid(),
            nullable=False,
            comment="UUID of user who started the session",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "COMMITTED",
                "ABORTED",
                name="quizeditsessionstatus",
                native_enum=False,
                length=20,
            ),
            nullable=False,
            comment="Session status (active/committed/aborted)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timestamp when session was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timestamp when session was last updated",
        ),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.quiz_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["draft_version_id"],
            ["quiz_version.quiz_version_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("edit_session_id"),
    )
    op.create_index(
        op.f("ix_quiz_edit_session_quiz_id"),
        "quiz_edit_session",
        ["quiz_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quiz_edit_session_started_by"),
        "quiz_edit_session",
        ["started_by"],
        unique=False,
    )

    op.add_column(
        "quiz",
        sa.Column(
            "current_version_id",
            sa.Uuid(),
            nullable=True,
            comment="Current published version of this quiz",
        ),
    )
    op.create_foreign_key(
        "fk_quiz_current_version",
        "quiz",
        "quiz_version",
        ["current_version_id"],
        ["quiz_version_id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "task",
        sa.Column(
            "quiz_version_id",
            sa.Uuid(),
            nullable=True,
            comment="Foreign key to quiz version",
        ),
    )
    op.create_index(
        "ix_task_quiz_version_order",
        "task",
        ["quiz_version_id", "order_index"],
        unique=False,
    )
    op.create_index("ix_task_quiz_id", "task", ["quiz_id"], unique=False)
    op.create_foreign_key(
        "fk_task_quiz_version",
        "task",
        "quiz_version",
        ["quiz_version_id"],
        ["quiz_version_id"],
        ondelete="CASCADE",
    )

    _backfill_versions()

    op.alter_column("task", "quiz_version_id", nullable=False)
    op.drop_index("ix_task_quiz_order", table_name="task")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(
        "ix_task_quiz_order",
        "task",
        ["quiz_id", "order_index"],
        unique=False,
    )
    op.drop_constraint("fk_task_quiz_version", "task", type_="foreignkey")
    op.drop_index("ix_task_quiz_id", table_name="task")
    op.drop_index("ix_task_quiz_version_order", table_name="task")
    op.drop_column("task", "quiz_version_id")

    op.drop_constraint("fk_quiz_current_version", "quiz", type_="foreignkey")
    op.drop_column("quiz", "current_version_id")

    op.drop_index(
        op.f("ix_quiz_edit_session_started_by"),
        table_name="quiz_edit_session",
    )
    op.drop_index(op.f("ix_quiz_edit_session_quiz_id"), table_name="quiz_edit_session")
    op.drop_table("quiz_edit_session")

    op.drop_index(op.f("ix_quiz_version_quiz_id"), table_name="quiz_version")
    op.drop_table("quiz_version")


def _backfill_versions() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT quiz_id, created_by, created_at FROM quiz"),
    ).fetchall()

    for row in rows:
        version_id = uuid.uuid4()
        created_at = row.created_at or datetime.now(timezone.utc)
        conn.execute(
            sa.text(
                """
                INSERT INTO quiz_version (
                    quiz_version_id,
                    quiz_id,
                    base_version_id,
                    version_number,
                    status,
                    created_by,
                    created_at,
                    committed_at
                )
                VALUES (
                    :quiz_version_id,
                    :quiz_id,
                    NULL,
                    1,
                    :status,
                    :created_by,
                    :created_at,
                    :committed_at
                )
                """,
            ),
            {
                "quiz_version_id": str(version_id),
                "quiz_id": str(row.quiz_id),
                "status": "PUBLISHED",
                "created_by": str(row.created_by),
                "created_at": created_at,
                "committed_at": created_at,
            },
        )

        conn.execute(
            sa.text(
                "UPDATE quiz SET current_version_id = :version_id WHERE quiz_id = :quiz_id",
            ),
            {"version_id": str(version_id), "quiz_id": str(row.quiz_id)},
        )

        conn.execute(
            sa.text(
                """
                UPDATE task
                SET quiz_version_id = :version_id
                WHERE quiz_id = :quiz_id
                """,
            ),
            {"version_id": str(version_id), "quiz_id": str(row.quiz_id)},
        )
