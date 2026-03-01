"""Schemas for auth token responses."""

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Response schema containing JWT token after successful authentication.

    Attributes:
        access_token: JWT token for authenticated requests
        token_type: Token type (always 'bearer' for JWT)
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
        examples=["bearer"],
    )
