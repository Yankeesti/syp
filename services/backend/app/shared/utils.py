"""Utility functions used across the application."""

from datetime import datetime
from decimal import Decimal
from typing import Any


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text."""
    import re

    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text


def paginate_query_params(page: int = 1, page_size: int = 20) -> dict[str, int]:
    """Calculate offset and limit for pagination."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    offset = (page - 1) * page_size
    return {"offset": offset, "limit": page_size}


def quantize_percent(value: Decimal | None) -> Decimal | None:
    """Quantize a percentage value to two decimal places.

    Returns None when input is None.
    """
    if value is None:
        return None
    return value.quantize(Decimal("0.01"))
