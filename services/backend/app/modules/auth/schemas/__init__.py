"""Auth module Pydantic schemas for API requests/responses."""

from app.modules.auth.schemas.magic_link import MagicLinkRequest, MagicLinkResponse
from app.modules.auth.schemas.token import TokenResponse
from app.modules.auth.schemas.report import ReportRequest, ReportResponse

__all__ = [
    "MagicLinkRequest",
    "MagicLinkResponse",
    "TokenResponse",
    "ReportRequest",
    "ReportResponse",
]
