"""Attempt model for learning progress tracking.

Based on Wiki Specification:
- Attempt represents a user's attempt to complete a quiz
- Has status (in_progress -> evaluated)
- References quiz_id and user_id (no FK to other modules)
- Tracks evaluation results (percentage)
"""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Index, DateTime, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptStatus(str, enum.Enum):
    """Attempt status for tracking completion state.

    Status machine: in_progress -> evaluated
    """

    IN_PROGRESS = "in_progress"  # User is still working on the attempt
    EVALUATED = "evaluated"  # Attempt has been evaluated


class Attempt(Base):
    """
    Attempt model representing a user's attempt to complete a quiz.

    Attributes:
        attempt_id: UUID primary key
        quiz_id: UUID reference to quiz (no FK - cross-module reference)
        user_id: UUID reference to user (no FK - cross-module reference)
        status: Attempt status (in_progress/evaluated)
        started_at: Timestamp when attempt was started
        evaluated_at: Timestamp when attempt was evaluated (nullable)
        total_percentage: Overall score as percentage (0-100, nullable until evaluated)

    Relationships:
        answers: One-to-many relationship to Answer (within learning module)
    """

    __tablename__ = "attempt"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        comment="UUID reference to quiz",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        comment="UUID reference to user",
    )

    status: Mapped[AttemptStatus] = mapped_column(
        SQLEnum(AttemptStatus, native_enum=False, length=20),
        nullable=False,
        default=AttemptStatus.IN_PROGRESS,
        comment="Attempt status (in_progress/evaluated)",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when attempt was started",
    )

    evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when attempt was evaluated",
    )

    total_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Overall score as percentage (0-100)",
    )

    # Relationships
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_attempt_user_id", "user_id"),
        Index("ix_attempt_quiz_id", "quiz_id"),
        Index("ix_attempt_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Attempt(attempt_id={self.attempt_id}, "
            f"quiz_id={self.quiz_id}, "
            f"user_id={self.user_id}, "
            f"status={self.status})>"
        )
