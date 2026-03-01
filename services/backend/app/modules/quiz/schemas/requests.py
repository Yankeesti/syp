"""FastAPI request schemas with framework-specific types.

These schemas handle request parsing (multipart/form-data, etc.) and are
tightly coupled to FastAPI. They are NOT pure DTOs.

Separated from pure Pydantic DTOs to maintain clear boundaries.
"""

from typing import Annotated

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, model_validator


class QuizCreateRequest(BaseModel):
    """Request schema for POST /quizzes with validation."""

    file: UploadFile | None = None
    user_description: str | None = None

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def check_file_or_description(self) -> "QuizCreateRequest":
        """Ensure at least one of file or user_description is provided."""
        if self.file is None and self.user_description is None:
            raise ValueError("Either 'file' or 'user_description' must be provided")
        return self

    @classmethod
    def as_form(
        cls,
        file: Annotated[UploadFile | None, File()] = None,
        user_description: Annotated[str | None, Form()] = None,
    ) -> "QuizCreateRequest":
        """Dependency for FastAPI to parse multipart/form-data."""
        return cls(file=file, user_description=user_description)
