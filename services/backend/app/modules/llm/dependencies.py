"""LLM module dependencies for FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends

from app.modules.llm.providers import LLMProviderDep
from app.modules.llm.service import LLMService


def get_llm_service(provider: LLMProviderDep) -> LLMService:
    """Dependency that provides an LLMService instance with the configured provider."""
    return LLMService(provider)


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
