"""Auth models package."""

from app.modules.auth.models.magic_link_token import MagicLinkToken
from app.modules.auth.models.user import User

__all__ = ["User", "MagicLinkToken"]
