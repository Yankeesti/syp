"""Magic link token model for authentication module."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MagicLinkToken(Base):
    """
    Magic Link Token model for passwordless authentication.

    Tokens are stored as SHA-256 hashes for security. The actual token is
    generated using secrets.token_urlsafe(32) and sent to the user via email.

    Attributes:
        id: UUID primary key
        token_hash: SHA-256 hash of the actual token (unique)
        email_hash: SHA-256 hash of the user's email address (unique)
        created_at: Timestamp when token was created
        expires_at: Timestamp when token expires (created_at + 5 minutes)
    """

    __tablename__ = "magic_link_token"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the magic link token",
    )

    email_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the user's email address",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the token was created",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,  # Index for cleanup queries
        comment="Timestamp when the token expires",
    )

    def __repr__(self) -> str:
        return (
            f"<MagicLinkToken(id={self.id}, "
            f"token_hash={self.token_hash[:8]}..., "
            f"expires_at={self.expires_at})>"
        )
