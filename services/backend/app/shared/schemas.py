"""Shared Pydantic schemas used across multiple modules."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """
    Decoded JWT token payload.

    Contains all authenticated user data extracted from the JWT.
    Designed for extensibility (role, permissions can be added later).

    Attributes:
        user_id: UUID of the authenticated user
    """

    user_id: uuid.UUID = Field(..., description="Authenticated user's UUID")

    def to_jwt_claims(self) -> dict:
        """
        Convert to JWT claims dictionary.

        Returns:
            Dictionary with claims ready for JWT encoding.
            Note: 'exp' (expiration) is added by the security layer.
        """
        return {"user_id": str(self.user_id)}

    @classmethod
    def from_jwt_claims(cls, claims: dict) -> TokenPayload:
        """
        Create TokenPayload from decoded JWT claims.

        Args:
            claims: Dictionary of decoded JWT claims

        Returns:
            TokenPayload instance

        Raises:
            KeyError: If required claim 'user_id' is missing
            ValueError: If 'user_id' is not a valid UUID
        """
        return cls(user_id=uuid.UUID(claims["user_id"]))
