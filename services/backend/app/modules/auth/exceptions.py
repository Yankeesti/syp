"""Domain exceptions for authentication module."""


class AuthError(Exception):
    """Base class for authentication domain errors."""


class MagicLinkTokenInvalidError(AuthError):
    """Raised when a magic link token is invalid or already used."""


class MagicLinkTokenExpiredError(AuthError):
    """Raised when a magic link token is expired."""


class UserNotRegisteredError(AuthError):
    """Raised when a user does not exist for a valid token."""
