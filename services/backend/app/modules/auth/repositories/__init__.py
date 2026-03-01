"""Authentication repositories package."""

from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.repositories.magic_link_token_repository import (
    MagicLinkTokenRepository,
)

__all__ = ["UserRepository", "MagicLinkTokenRepository"]
