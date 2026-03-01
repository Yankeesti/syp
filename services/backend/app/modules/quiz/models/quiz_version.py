"""Quiz version model for draft/published snapshots."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizVersionStatus(str, enum.Enum):
    """Version status for a quiz snapshot."""

    DRAFT = "draft"
    PUBLISHED = "published"


class QuizVersion(Base):
    """Version snapshot of a quiz with its tasks."""

    __tablename__ = "quiz_version"

    quiz_version_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz.quiz_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to quiz",
    )

    base_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quiz_version.quiz_version_id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional base version for drafts",
    )

    version_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Sequential version number (assigned on commit)",
    )

    status: Mapped[QuizVersionStatus] = mapped_column(
        SQLEnum(QuizVersionStatus, native_enum=False, length=20),
        nullable=False,
        default=QuizVersionStatus.DRAFT,
        comment="Version status (draft/published)",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is the current version for the quiz",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        comment="UUID of user who created the version",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when version was created",
    )

    committed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when version was committed",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="versions",
        foreign_keys=[quiz_id],
    )

    base_version: Mapped["QuizVersion | None"] = relationship(
        "QuizVersion",
        remote_side=[quiz_version_id],
        foreign_keys=[base_version_id],
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="Task.order_index",
    )

    def __repr__(self) -> str:
        return (
            f"<QuizVersion(quiz_version_id={self.quiz_version_id}, "
            f"quiz_id={self.quiz_id}, "
            f"status={self.status})>"
        )
