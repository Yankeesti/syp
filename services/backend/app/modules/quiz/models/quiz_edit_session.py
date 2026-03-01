"""Quiz edit session model for draft editing workflow."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizEditSessionStatus(str, enum.Enum):
    """Edit session status values."""

    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"


class QuizEditSession(Base):
    """Edit session for staged quiz changes."""

    __tablename__ = "quiz_edit_session"

    edit_session_id: Mapped[uuid.UUID] = mapped_column(
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

    draft_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_version.quiz_version_id", ondelete="CASCADE"),
        nullable=False,
        comment="Draft version associated with this session",
    )

    started_by: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
        comment="UUID of user who started the session",
    )

    status: Mapped[QuizEditSessionStatus] = mapped_column(
        SQLEnum(QuizEditSessionStatus, native_enum=False, length=20),
        nullable=False,
        default=QuizEditSessionStatus.ACTIVE,
        comment="Session status (active/committed/aborted)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when session was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when session was last updated",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="edit_sessions",
    )

    draft_version: Mapped["QuizVersion"] = relationship(
        "QuizVersion",
        foreign_keys=[draft_version_id],
    )

    def __repr__(self) -> str:
        return (
            f"<QuizEditSession(edit_session_id={self.edit_session_id}, "
            f"quiz_id={self.quiz_id}, "
            f"status={self.status})>"
        )
