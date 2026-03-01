"""Pydantic schemas for share link DTOs.

These schemas define the data structure for quiz share links.
Used for creating shareable magic links with configurable access control.
"""

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field


class ShareLinkCreateRequest(BaseModel):
    """Input schema for creating a share link.

    Attributes:
        duration: Optional duration for how long the link is valid.
                 Accepts seconds as int/float, or ISO 8601 duration string (e.g., "P1D" for 1 day, "PT12H" for 12 hours).
                 If null, the link never expires.
        max_uses: Optional maximum number of uses (null = unlimited)

    Examples:
        Seconds (1 day):
            {"duration": 86400, "max_uses": 10}
        ISO 8601 string (1 day, 12 hours):
            {"duration": "P1DT12H", "max_uses": 5}
        No expiration:
            {"duration": null, "max_uses": 10}
    """

    duration: timedelta | None = Field(
        default=None,
        description="Link validity duration. Accepts seconds (int/float) or ISO 8601 duration string (e.g., 'P1D', 'PT12H')",
    )
    max_uses: int | None = Field(
        default=None,
        ge=1,
        description="Optional maximum number of uses (null = unlimited)",
    )


class ShareLinkDto(BaseModel):
    """Output schema for share link details.

    Returned when creating or listing share links.
    Includes full URL for easy sharing.
    """

    share_link_id: UUID
    quiz_id: UUID
    token: str
    url: str
    created_at: datetime
    expires_at: datetime | None
    max_uses: int | None
    current_uses: int
    is_active: bool

    model_config = {"from_attributes": True}


class ShareLinkInfoDto(BaseModel):
    """Public output schema for share link validation.

    Used by the public endpoint to display quiz info before redemption.
    Does not expose sensitive information like token internals.
    """

    quiz_id: UUID | None = None
    quiz_title: str
    quiz_topic: str
    is_valid: bool
    error_message: str | None = None
