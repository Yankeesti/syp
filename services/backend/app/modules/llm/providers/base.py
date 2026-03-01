"""Base abstractions for LLM providers."""

from enum import Enum
from typing import Protocol


class ModelRole(str, Enum):
    """Logical model roles, mapped to concrete model names by each provider."""

    GENERATION = "generation"
    UTILITY = "utility"


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""


class LLMAuthenticationError(LLMProviderError):
    """Raised when authentication with the LLM provider fails."""


class LLMProviderUnavailableError(LLMProviderError):
    """Raised when the LLM provider is unreachable."""


class LLMProvider(Protocol):
    """Protocol defining the interface every LLM provider must implement."""

    async def call(
        self,
        messages: list[dict[str, str]],
        role: ModelRole,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request to the provider.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            role: The logical model role to use.
            temperature: Controls randomness (0.0=deterministic, 1.0=creative).

        Returns:
            The LLM response content as string.

        Raises:
            LLMProviderError: On general provider errors.
            LLMAuthenticationError: On authentication failure.
            LLMProviderUnavailableError: When the provider is unreachable.
        """
        ...

    async def health_check(self) -> dict:
        """Check provider connectivity and return status info.

        Returns:
            Dict with provider status information.

        Raises:
            LLMProviderUnavailableError: When the provider is unreachable.
        """
        ...
