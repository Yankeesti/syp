"""Quiz model for content management.

Based on Wiki Specification:
- Quiz represents a collection of tasks (questions)
- Has state machine (private -> protected -> public)
- Has status for generation progress (pending -> generating -> completed/failed)
- Owned by creator (user_id stored, but no FK to auth module)
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizState(str, enum.Enum):
    """Quiz visibility state - can only progress forward.

    State machine: private -> protected -> public
    """

    PRIVATE = "private"  # Only owner can access
    PROTECTED = "protected"  # Shared with specific users
    PUBLIC = "public"  # Public access


class QuizStatus(str, enum.Enum):
    """Quiz generation status.

    Status machine: pending -> generating -> completed/failed
    """

    PENDING = "pending"  # Creation requested, not started
    GENERATING = "generating"  # LLM is generating tasks
    COMPLETED = "completed"  # Generation finished successfully
    FAILED = "failed"  # Generation failed


class Quiz(Base):
    """
    Quiz model representing a collection of tasks.

    Attributes:
        quiz_id: UUID primary key
        title: Quiz title (generated or provided)
        topic: Main topic/subject of the quiz
        state: Visibility state (private/protected/public)
        status: Generation status (pending/generating/completed/failed)
        created_by: UUID of creator (no FK to auth module - cross-module reference)
        created_at: Timestamp when quiz was created
        updated_at: Timestamp when quiz was last updated

    Relationships:
        tasks: One-to-many relationship to Task (within quiz module)
        ownerships: One-to-many relationship to QuizOwnership (shared access)
    """

    __tablename__ = "quiz"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Quiz title",
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Main topic/subject of the quiz",
    )

    state: Mapped[QuizState] = mapped_column(
        SQLEnum(QuizState, native_enum=False, length=20),
        nullable=False,
        default=QuizState.PRIVATE,
        comment="Visibility state (private/protected/public)",
    )

    status: Mapped[QuizStatus] = mapped_column(
        SQLEnum(QuizStatus, native_enum=False, length=20),
        nullable=False,
        default=QuizStatus.PENDING,
        comment="Generation status (pending/generating/completed/failed)",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
        comment="UUID of creator",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when quiz was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when quiz was last updated",
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Task.order_index",
    )

    versions: Mapped[list["QuizVersion"]] = relationship(
        "QuizVersion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        foreign_keys="QuizVersion.quiz_id",
    )

    edit_sessions: Mapped[list["QuizEditSession"]] = relationship(
        "QuizEditSession",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    ownerships: Mapped[list["QuizOwnership"]] = relationship(
        "QuizOwnership",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    share_links: Mapped[list["ShareLink"]] = relationship(
        "ShareLink",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Quiz(quiz_id={self.quiz_id}, "
            f"title='{self.title}', "
            f"state={self.state}, "
            f"status={self.status})>"
        )
