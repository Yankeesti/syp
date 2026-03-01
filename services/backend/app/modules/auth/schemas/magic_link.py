"""Schemas for magic link requests and responses."""

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """
    Request schema for magic link generation.

    Attributes:
        email: User's email address (validated for correct format)
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )


class MagicLinkResponse(BaseModel):
    """
    Response schema after requesting a magic link.

    Attributes:
        message: Generic success message to display to user
        expires_in: Seconds until the magic link expires
    """

    message: str = Field(
        ...,
        description="Success message",
        examples=["If the email is registered, a magic link has been sent"],
    )
    expires_in: int = Field(
        ...,
        description="Seconds until the magic link expires",
        examples=[300],
    )
