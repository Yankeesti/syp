"""Quiz ownership repository for database operations.

This module provides data access layer for QuizOwnership entities.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, UniqueConstraint, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OwnershipRole(str, enum.Enum):
    """Ownership role with hierarchy: VIEWER < EDITOR < OWNER."""

    VIEWER = ("viewer", 1)
    EDITOR = ("editor", 2)
    OWNER = ("owner", 3)

    def __new__(cls, value: str, level: int):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._level = level
        return obj

    @property
    def level(self) -> int:
        """Get the hierarchy level for this role (higher = more permissions)."""
        return self._level

    def has_permission_for(self, required_role: "OwnershipRole") -> bool:
        """Check if this role has sufficient permission for the required role."""
        return self._level >= required_role._level


class QuizOwnership(Base):

    __tablename__ = "quiz_ownership"

    ownership_id: Mapped[uuid.UUID] = mapped_column(
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

    user_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
        comment="UUID of user (no FK - cross-module reference to auth.user)",
    )

    role: Mapped[OwnershipRole] = mapped_column(
        SQLEnum(OwnershipRole, native_enum=False, length=20),
        nullable=False,
        comment="Access level (owner/editor/viewer)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when ownership was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when ownership was last updated",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="ownerships",
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("quiz_id", "user_id", name="uq_quiz_ownership_quiz_user"),
        Index("ix_quiz_ownership_user_role", "user_id", "role"),
    )
