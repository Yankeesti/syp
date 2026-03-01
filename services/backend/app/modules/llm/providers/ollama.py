"""Ollama LLM provider implementation."""

import logging

import httpx

from app.core.config import get_settings
from app.modules.llm.providers.base import (
    ModelRole,
    LLMAuthenticationError,
    LLMProviderError,
    LLMProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class OllamaProvider:
    """LLM provider implementation for Ollama API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_url = settings.llm_api_url
        self._auth_user = settings.llm_auth_user
        self._auth_password = settings.llm_auth_password
        self._timeout = settings.llm_timeout_seconds
        self._model_map: dict[ModelRole, str] = {
            ModelRole.GENERATION: settings.llm_ollama_generation_model,
            ModelRole.UTILITY: settings.llm_ollama_utility_model,
        }

    async def call(
        self,
        messages: list[dict[str, str]],
        role: ModelRole,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            role: The logical model role to use.
            temperature: Controls randomness (0.0=deterministic, 1.0=creative).

        Returns:
            The LLM response content as string.
        """
        model_name = self._model_map[role]
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "temperature": temperature,
        }

        auth = httpx.BasicAuth(self._auth_user, self._auth_password)

        try:
            async with httpx.AsyncClient(timeout=self._timeout, auth=auth) as client:
                response = await client.post(self._api_url, json=payload)

                if response.status_code == 401:
                    raise LLMAuthenticationError(
                        "Authentifizierung am KI-Server fehlgeschlagen.",
                    )

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    body_text = e.response.text
                    try:
                        body_json = e.response.json()
                    except ValueError:
                        body_json = None

                    logger.error(
                        "Ollama API Error: %s %s -> %s\nResponse: %s",
                        e.request.method,
                        e.request.url,
                        e.response.status_code,
                        body_json if body_json is not None else body_text,
                        exc_info=True,
                    )
                    raise LLMProviderError(
                        f"Ollama API error: {e.response.status_code}",
                    ) from e

                result = response.json()
                return result["message"]["content"]

        except (LLMAuthenticationError, LLMProviderError):
            raise
        except httpx.ConnectError as e:
            raise LLMProviderUnavailableError(
                f"Ollama server nicht erreichbar: {e}",
            ) from e
        except Exception as e:
            raise LLMProviderError(f"Ollama call failed: {e}") from e

    async def health_check(self) -> dict:
        """Check Ollama connectivity by pinging the tags API."""
        test_url = self._api_url.replace("/api/chat", "/api/tags")
        auth = httpx.BasicAuth(self._auth_user, self._auth_password)

        try:
            async with httpx.AsyncClient(timeout=10.0, auth=auth) as client:
                resp = await client.get(test_url)
                resp.raise_for_status()

                return {
                    "status": "online",
                    "provider": "ollama",
                    "message": "Verbindung zum FH Ollama Server steht!",
                    "info": resp.json(),
                }
        except Exception as e:
            raise LLMProviderUnavailableError(
                f"Verbindung fehlgeschlagen: {e}. VPN aktiv?",
            ) from e
