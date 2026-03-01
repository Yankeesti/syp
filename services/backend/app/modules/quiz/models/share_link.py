"""Share link model for quiz sharing.

Allows quiz owners to create shareable magic links that grant viewer access.
Links can have expiration dates and usage limits.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ShareLink(Base):
    """
    Share link model for sharing quizzes via magic links.

    Attributes:
        share_link_id: UUID primary key
        quiz_id: UUID of the quiz being shared (FK to quiz)
        token: Unique cryptographic token for the share link
        created_by: UUID of creator (no FK to auth module - cross-module reference)
        created_at: Timestamp when link was created
        expires_at: Optional expiration timestamp (null = never expires)
        max_uses: Optional maximum number of uses (null = unlimited)
        current_uses: Current number of times the link has been used
        is_active: Whether link is active (can be revoked by setting to false)

    Relationships:
        quiz: Many-to-one relationship to Quiz
    """

    __tablename__ = "quiz_share_link"

    share_link_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz.quiz_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="UUID of the quiz being shared",
    )

    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique cryptographic token for the share link",
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
        comment="Timestamp when link was created",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional expiration timestamp (null = never expires)",
    )

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Optional maximum number of uses (null = unlimited)",
    )

    current_uses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current number of times the link has been used",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether link is active (can be revoked)",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="share_links",
    )

    def __repr__(self) -> str:
        return (
            f"<ShareLink(share_link_id={self.share_link_id}, "
            f"quiz_id={self.quiz_id}, "
            f"is_active={self.is_active}, "
            f"current_uses={self.current_uses})>"
        )
