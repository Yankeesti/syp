"""LLM Service for quiz generation."""

import json
import logging

from pydantic import ValidationError

from app.modules.llm.providers.base import (
    LLMProvider,
    LLMProviderError,
    ModelRole,
)
from app.modules.llm.prompts import (
    DEFAULT_TOPIC,
    USER_PROMPT_TOPIC_TEMPLATE,
    USER_PROMPT_DOCUMENT_TEMPLATE,
    SystemPromptBuilder,
    CorrectionPromptBuilder,
)
from app.shared.quiz_generation import QuizGenerationSpec, QuizUpsertDto
from app.modules.llm.prompts.constants import (
    DEFAULT_NUM_QUESTIONS,
    TASK_NUMBER_EXTRACTION_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based quiz generation using an injected provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def health_check(self) -> dict:
        """Delegate health check to the underlying provider."""
        return await self._provider.health_check()

    async def _build_system_prompt(self, spec: QuizGenerationSpec) -> str:
        """Baut den System-Prompt dynamisch basierend auf den angeforderten Task-Typen."""
        num_questions = await self.extract_task_count(spec)
        has_file = bool(spec.file_content)
        has_description = bool(spec.user_description)

        return (
            SystemPromptBuilder()
            .with_role(spec.task_types)
            .with_objective(
                num_questions=num_questions,
                has_file=has_file,
                has_description=has_description,
            )
            .with_process(
                num_questions=num_questions,
                task_types=spec.task_types,
                has_file=has_file,
            )
            .with_output_format()
            .with_task_schemas(spec.task_types)
            .with_final_constraints(num_questions=num_questions)
            .build()
        )

    def _build_user_prompt(
        self,
        spec: QuizGenerationSpec,
    ) -> list[dict[str, str]]:
        topic = spec.user_description or DEFAULT_TOPIC
        user_prompt = USER_PROMPT_TOPIC_TEMPLATE.format(topic=topic)
        messages: list[dict[str, str]] = []

        if spec.file_content:
            try:
                context_text = spec.file_content.decode("utf-8")
                file_content = USER_PROMPT_DOCUMENT_TEMPLATE.format(
                    content=context_text,
                )
                messages.append(
                    {"role": "user", "content": "Dokument: " + file_content},
                )
            except UnicodeDecodeError as e:
                logger.warning("Datei-Inhalt konnte nicht dekodiert werden: %s", e)

        messages.append({"role": "user", "content": user_prompt})

        return messages

    async def generate_quiz(
        self,
        spec: QuizGenerationSpec,
        max_retries: int = 4,
    ) -> QuizUpsertDto:
        """Nimmt die Spezifikation entgegen und nutzt das LLM.

        Args:
            spec: The quiz generation specification.
            max_retries: Maximum number of retry attempts on validation errors.

        Returns:
            The validated QuizUpsertDto.

        Raises:
            ValueError: If LLM returns invalid format after all retries.
            LLMProviderError: On provider errors.
        """
        system_prompt = await self._build_system_prompt(spec)
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        messages.extend(self._build_user_prompt(spec))

        requested_types_str = ", ".join([t.value for t in spec.task_types])
        logger.info(
            "LLM quiz generation started (task_types=%s, has_file=%s)",
            requested_types_str,
            bool(spec.file_content),
        )
        logger.debug("LLM system prompt: %s", system_prompt)
        logger.debug("LLM user messages: %s", messages)

        # Temperature based on input
        temperature = 0.2 if spec.file_content else 0.6

        try:
            for attempt in range(max_retries + 1):
                raw_response = await self._provider.call(
                    messages,
                    ModelRole.GENERATION,
                    temperature=temperature,
                )
                logger.debug("LLM response received:\n%s", raw_response)

                try:
                    return QuizUpsertDto.model_validate_json(raw_response)
                except ValidationError as e:
                    if attempt < max_retries:
                        correction_prompt = (
                            CorrectionPromptBuilder()
                            .with_validation_errors(str(e))
                            .with_task_types(spec.task_types)
                            .build()
                        )
                        messages.append({"role": "assistant", "content": raw_response})
                        messages.append({"role": "user", "content": correction_prompt})
                        logger.warning(
                            "LLM validation failed, retry %d/%d: %s",
                            attempt + 1,
                            max_retries,
                            str(e),
                        )
                    else:
                        logger.error("Pydantic Validierungsfehler: %s", e.json())
                        raise ValueError(
                            "Die KI hat ein ungültiges Datenformat geliefert.",
                        ) from e

        except LLMProviderError as e:
            logger.error("LLM provider error: %s", e)
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error("Fehler im LLMService: %s", e)
            raise

        raise ValueError("Die KI hat ein ungültiges Datenformat geliefert.")

    async def extract_task_count(
        self,
        spec: QuizGenerationSpec,
    ) -> int:
        """Extract desired task count from the user prompt via LLM."""
        user_prompt = spec.user_description
        if not user_prompt:
            return DEFAULT_NUM_QUESTIONS
        messages = [
            {"role": "system", "content": TASK_NUMBER_EXTRACTION_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Temperature 0.0: Deterministische Extraktion einer Zahl
        raw_response = await self._provider.call(
            messages,
            ModelRole.UTILITY,
            temperature=0.0,
        )

        try:
            payload = json.loads(raw_response)
            extracted_count = int(payload.get("num_questions", 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            return DEFAULT_NUM_QUESTIONS

        return extracted_count if extracted_count > 0 else DEFAULT_NUM_QUESTIONS
