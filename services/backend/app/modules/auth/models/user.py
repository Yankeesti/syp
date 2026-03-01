"""User model for authentication module."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    User model representing a natural person authenticated via Magic Link.

    Attributes:
        user_id: UUID primary key and reference point for all data relationships
        email_hash: Hash of email address; used solely to assign Magic Link dispatch
                   to an existing account
        created_at: Timestamp when the user was created (optional, for auditing)
    """

    __tablename__ = "user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key and reference point for all data relationships",
    )

    email_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hash is 64 characters in hex
        unique=True,
        nullable=False,
        index=True,  # Index for fast lookups during Magic Link dispatch
        comment="Hash of email address for Magic Link assignment",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the user account was created",
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email_hash={self.email_hash[:8]}...)>"
