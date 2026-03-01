"""Tests for CorrectionPromptBuilder."""

import pytest

from app.modules.llm.prompts.correction import CorrectionPromptBuilder
from app.modules.llm.prompts.task_blocks import (
    MULTIPLE_CHOICE_SCHEMA,
    FREE_TEXT_SCHEMA,
    CLOZE_SCHEMA,
)
from app.modules.quiz.models.task import TaskType


pytestmark = pytest.mark.unit


class TestCorrectionPromptBuilder:
    """Tests for CorrectionPromptBuilder class."""

    def test_with_validation_errors_includes_error_message(self):
        """Test that validation errors are included in the prompt."""
        error_str = "2 validation errors for Quiz\ntitle\n  Field required"

        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors(error_str)
            .with_task_types([TaskType.MULTIPLE_CHOICE])
            .build()
        )

        assert "2 validation errors for Quiz" in prompt
        assert "title" in prompt
        assert "Field required" in prompt

    def test_with_task_types_single_multiple_choice(self):
        """Test that only MC schema is included when only MC is requested."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.MULTIPLE_CHOICE])
            .build()
        )

        assert "multiple_choice" in prompt
        assert MULTIPLE_CHOICE_SCHEMA in prompt
        assert FREE_TEXT_SCHEMA not in prompt
        assert CLOZE_SCHEMA not in prompt

    def test_with_task_types_single_free_text(self):
        """Test that only free text schema is included when only free text is requested."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.FREE_TEXT])
            .build()
        )

        assert "free_text" in prompt
        assert FREE_TEXT_SCHEMA in prompt
        assert MULTIPLE_CHOICE_SCHEMA not in prompt
        assert CLOZE_SCHEMA not in prompt

    def test_with_task_types_single_cloze(self):
        """Test that only cloze schema is included when only cloze is requested."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.CLOZE])
            .build()
        )

        assert "cloze" in prompt
        assert CLOZE_SCHEMA in prompt
        assert MULTIPLE_CHOICE_SCHEMA not in prompt
        assert FREE_TEXT_SCHEMA not in prompt

    def test_with_task_types_multiple(self):
        """Test that multiple schemas are included when multiple types are requested."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.FREE_TEXT, TaskType.CLOZE])
            .build()
        )

        assert FREE_TEXT_SCHEMA in prompt
        assert CLOZE_SCHEMA in prompt
        assert MULTIPLE_CHOICE_SCHEMA not in prompt

    def test_with_task_types_all(self):
        """Test that all schemas are included when all types are requested."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types(
                [TaskType.MULTIPLE_CHOICE, TaskType.FREE_TEXT, TaskType.CLOZE],
            )
            .build()
        )

        assert MULTIPLE_CHOICE_SCHEMA in prompt
        assert FREE_TEXT_SCHEMA in prompt
        assert CLOZE_SCHEMA in prompt

    def test_build_includes_quiz_structure(self):
        """Test that the quiz structure schema is always included."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.MULTIPLE_CHOICE])
            .build()
        )

        assert "QUIZ-STRUKTUR" in prompt
        assert '"title"' in prompt
        assert '"topic"' in prompt
        assert '"tasks"' in prompt

    def test_build_includes_intro_and_outro(self):
        """Test that the correction prompt includes intro and outro."""
        prompt = (
            CorrectionPromptBuilder()
            .with_validation_errors("some error")
            .with_task_types([TaskType.MULTIPLE_CHOICE])
            .build()
        )

        assert "Deine vorherige JSON-Antwort war ungültig" in prompt
        assert "Antworte NUR mit dem korrigierten JSON" in prompt

    def test_builder_is_chainable(self):
        """Test that builder methods return self for chaining."""
        builder = CorrectionPromptBuilder()

        result1 = builder.with_validation_errors("error")
        assert result1 is builder

        result2 = builder.with_task_types([TaskType.MULTIPLE_CHOICE])
        assert result2 is builder
