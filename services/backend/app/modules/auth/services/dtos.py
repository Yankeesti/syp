"""Service-layer DTOs for authentication module."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MagicLinkResult:
    """Result of a magic link request in the service layer."""

    expires_in: int
    already_registered: bool | None = None


@dataclass(frozen=True, slots=True)
class TokenResult:
    """Result of magic link verification in the service layer."""

    access_token: str
    token_type: str
