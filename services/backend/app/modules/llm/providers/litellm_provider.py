"""LiteLLM provider for cloud LLM APIs (OpenAI, Anthropic, Google, etc.)."""

import litellm

from app.core.config import get_settings
from app.modules.llm.providers.base import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMProviderUnavailableError,
    ModelRole,
)


class LiteLLMProvider:
    """Provider using LiteLLM for OpenAI, Anthropic, Google, etc."""

    def __init__(self) -> None:
        settings = get_settings()
        self._timeout = settings.llm_timeout_seconds
        self._model_map = {
            ModelRole.GENERATION: settings.llm_litellm_generation_model,
            ModelRole.UTILITY: settings.llm_litellm_utility_model,
        }

        # Set API keys for LiteLLM
        if settings.llm_openai_api_key:
            litellm.openai_key = settings.llm_openai_api_key
        if settings.llm_anthropic_api_key:
            litellm.anthropic_key = settings.llm_anthropic_api_key
        if settings.llm_google_api_key:
            litellm.vertex_key = settings.llm_google_api_key

    async def call(
        self,
        messages: list[dict[str, str]],
        role: ModelRole,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request via LiteLLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            role: The logical model role to use.
            temperature: Controls randomness (0.0=deterministic, 1.0=creative).

        Returns:
            The LLM response content as string.

        Raises:
            LLMAuthenticationError: On authentication failure.
            LLMProviderUnavailableError: When the provider is unreachable.
            LLMProviderError: On general provider errors.
        """
        model = self._model_map[role]

        # Determine response format based on model
        # OpenAI models use response_format, Ollama models use format
        extra_kwargs: dict = {}
        if model.startswith("ollama/"):
            extra_kwargs["format"] = "json"
        else:
            extra_kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=self._timeout,
                **extra_kwargs,
            )
            return response.choices[0].message.content
        except litellm.AuthenticationError as e:
            raise LLMAuthenticationError(str(e)) from e
        except litellm.APIConnectionError as e:
            raise LLMProviderUnavailableError(str(e)) from e
        except Exception as e:
            raise LLMProviderError(str(e)) from e

    async def health_check(self) -> dict:
        """Check provider connectivity and return status info.

        Returns:
            Dict with provider status information.

        Raises:
            LLMProviderUnavailableError: When the provider is unreachable.
        """
        model = self._model_map[ModelRole.UTILITY]
        try:
            await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                timeout=10.0,
            )
            return {
                "status": "online",
                "provider": "litellm",
                "model": model,
            }
        except litellm.AuthenticationError as e:
            raise LLMAuthenticationError(
                f"LiteLLM authentication failed: {e}",
            ) from e
        except Exception as e:
            raise LLMProviderUnavailableError(
                f"LiteLLM health check failed: {e}",
            ) from e
