"""LLM Provider implementations."""

from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.modules.llm.providers.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Factory that returns the configured LLM provider instance.

    Reads ``settings.llm_provider`` and instantiates the matching provider.
    Can be used as a FastAPI dependency or called directly in background tasks.

    Supported providers:
        - "ollama": OllamaProvider (FH server with BasicAuth)
        - "litellm": LiteLLMProvider (OpenAI, Anthropic, Google, local Ollama)
    """
    settings = get_settings()

    match settings.llm_provider:
        case "ollama":
            from app.modules.llm.providers.ollama import OllamaProvider

            return OllamaProvider()
        case "litellm":
            from app.modules.llm.providers.litellm_provider import LiteLLMProvider

            return LiteLLMProvider()
        case _:
            raise ValueError(
                f"Unknown LLM provider: '{settings.llm_provider}'. "
                f"Supported: 'ollama', 'litellm'",
            )


LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
