"""Helpers for integration tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt

from app.core.config import get_settings
from app.modules.quiz.schemas import (
    ClozeBlankCreate,
    ClozeTaskCreate,
    FreeTextTaskCreate,
    MultipleChoiceOptionCreate,
    MultipleChoiceTaskCreate,
    QuizUpsertDto,
)
from app.shared.schemas import TokenPayload


def build_default_quiz_output(topic: str = "Testing") -> QuizUpsertDto:
    """Create a deterministic quiz output for LLM mocking."""
    return QuizUpsertDto(
        title=f"Quiz: {topic}",
        topic=topic,
        tasks=[
            MultipleChoiceTaskCreate(
                type="multiple_choice",
                prompt=f"Welche Aussage über {topic} ist korrekt?",
                topic_detail=topic,
                options=[
                    MultipleChoiceOptionCreate(
                        text="Korrekte Antwort",
                        is_correct=True,
                        explanation="Diese Antwort ist korrekt.",
                    ),
                    MultipleChoiceOptionCreate(
                        text="Falsche Antwort 1",
                        is_correct=False,
                        explanation=None,
                    ),
                    MultipleChoiceOptionCreate(
                        text="Falsche Antwort 2",
                        is_correct=False,
                        explanation=None,
                    ),
                ],
            ),
            FreeTextTaskCreate(
                type="free_text",
                prompt=f"Erkläre kurz {topic}.",
                topic_detail=topic,
                reference_answer=f"{topic} ist ein Test-Thema.",
            ),
            ClozeTaskCreate(
                type="cloze",
                prompt=f"Fülle die Lücken zu {topic}.",
                topic_detail=topic,
                template_text=(
                    f"Bei {{{{blank_1}}}} handelt es sich um {topic}. "
                    f"Es steht im Zusammenhang mit {{{{blank_2}}}}."
                ),
                blanks=[
                    ClozeBlankCreate(position=1, expected_value=topic),
                    ClozeBlankCreate(position=2, expected_value="Lernen"),
                ],
            ),
        ],
    )


def build_answer_payload(task: dict[str, Any]) -> dict[str, Any]:
    """Build a correct answer payload for a task response dict."""
    task_type = task["type"]

    if task_type == "multiple_choice":
        selected_ids = [
            option["option_id"]
            for option in task.get("options", [])
            if option.get("is_correct")
        ]
        return {
            "type": "multiple_choice",
            "data": {"selected_option_ids": selected_ids},
        }

    if task_type == "free_text":
        return {
            "type": "free_text",
            "data": {"text_response": task.get("reference_answer", "Testantwort")},
        }

    if task_type == "cloze":
        provided_values = [
            {
                "blank_id": blank["blank_id"],
                "value": blank["expected_value"],
            }
            for blank in task.get("blanks", [])
        ]
        return {
            "type": "cloze",
            "data": {"provided_values": provided_values},
        }

    raise ValueError(f"Unsupported task type: {task_type}")


def build_expired_token(user_id: UUID, seconds: int = -3600) -> str:
    """Create a JWT that is already expired."""
    settings = get_settings()
    payload = TokenPayload(user_id=user_id).to_jwt_claims()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
