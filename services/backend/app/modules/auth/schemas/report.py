"""Schemas for user error reports."""

from pydantic import BaseModel, EmailStr, Field


class ReportRequest(BaseModel):
    """Payload sent when reporting an error."""

    message: str = Field(..., description="User-visible description of the issue")
    contact_email: EmailStr | None = Field(
        None,
        description="Optional contact email for follow-up",
    )


class ReportResponse(BaseModel):
    message: str
