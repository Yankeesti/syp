"""Tests for LLMService retry mechanism."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.llm.providers.base import ModelRole
from app.modules.llm.service import LLMService
from app.modules.quiz.models.task import TaskType
from app.modules.quiz.schemas.quiz_input import QuizGenerationSpec


pytestmark = pytest.mark.unit


class TestLLMServiceRetry:
    """Tests for LLMService.generate_quiz retry mechanism."""

    @pytest.fixture
    def mock_provider(self):
        """Mock LLM provider."""
        provider = AsyncMock()
        provider.call = AsyncMock()
        provider.health_check = AsyncMock(return_value={"status": "ok"})
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        """Create LLMService instance with mocked provider."""
        svc = LLMService(provider=mock_provider)
        # Mock extract_task_count to avoid an extra provider.call
        svc.extract_task_count = AsyncMock(return_value=5)
        return svc

    @pytest.fixture
    def valid_quiz_json(self):
        """Valid quiz JSON response."""
        return json.dumps(
            {
                "title": "Test Quiz",
                "topic": "Test Topic",
                "tasks": [
                    {
                        "type": "multiple_choice",
                        "prompt": "Test question?",
                        "topic_detail": "Test detail",
                        "options": [
                            {
                                "text": "Option A",
                                "is_correct": True,
                                "explanation": "Correct",
                            },
                            {
                                "text": "Option B",
                                "is_correct": False,
                                "explanation": "Wrong",
                            },
                        ],
                    },
                ],
            },
        )

    @pytest.fixture
    def invalid_quiz_json(self):
        """Invalid quiz JSON response (missing required field)."""
        return json.dumps(
            {
                "title": 123,  # Should be string
                "topic": "Test Topic",
                "tasks": [],
            },
        )

    @pytest.fixture
    def generation_spec(self):
        """Quiz generation spec."""
        return QuizGenerationSpec(
            task_types=[TaskType.MULTIPLE_CHOICE],
            user_description="Test description",
        )

    async def test_generate_quiz_success_on_first_try(
        self,
        service,
        mock_provider,
        generation_spec,
        valid_quiz_json,
    ):
        """Test that generate_quiz succeeds on first try with valid JSON."""
        mock_provider.call.return_value = valid_quiz_json

        result = await service.generate_quiz(generation_spec)

        assert result.title == "Test Quiz"
        assert result.topic == "Test Topic"
        assert len(result.tasks) == 1
        mock_provider.call.assert_called_once()

    async def test_generate_quiz_retries_on_validation_error(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
        valid_quiz_json,
    ):
        """Test that generate_quiz retries when validation fails."""
        mock_provider.call.side_effect = [invalid_quiz_json, valid_quiz_json]

        result = await service.generate_quiz(generation_spec)

        assert result.title == "Test Quiz"
        assert mock_provider.call.call_count == 2

    async def test_generate_quiz_extends_message_history_on_retry(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
        valid_quiz_json,
    ):
        """Test that message history is extended on retry."""
        call_messages = []

        async def capture_messages(messages, role, temperature=0.7):
            call_messages.append([m.copy() for m in messages])
            if len(call_messages) == 1:
                return invalid_quiz_json
            return valid_quiz_json

        mock_provider.call.side_effect = capture_messages

        await service.generate_quiz(generation_spec)

        # First call: system + user prompt = 2 messages
        assert len(call_messages[0]) == 2
        assert call_messages[0][0]["role"] == "system"
        assert call_messages[0][1]["role"] == "user"

        # Second call: system + user prompt + assistant response + correction = 4 messages
        assert len(call_messages[1]) == 4
        assert call_messages[1][0]["role"] == "system"
        assert call_messages[1][1]["role"] == "user"
        assert call_messages[1][2]["role"] == "assistant"
        assert call_messages[1][2]["content"] == invalid_quiz_json
        assert call_messages[1][3]["role"] == "user"
        assert "validation error" in call_messages[1][3]["content"].lower()

    async def test_generate_quiz_correction_prompt_contains_task_schemas(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
        valid_quiz_json,
    ):
        """Test that correction prompt contains only requested task schemas."""
        call_messages = []

        async def capture_messages(messages, role, temperature=0.7):
            call_messages.append([m.copy() for m in messages])
            if len(call_messages) == 1:
                return invalid_quiz_json
            return valid_quiz_json

        mock_provider.call.side_effect = capture_messages

        await service.generate_quiz(generation_spec)

        # Check correction prompt contains MC schema (last message of second call)
        correction_prompt = call_messages[1][-1]["content"]
        assert "multiple_choice" in correction_prompt
        # Should not contain other types since only MC was requested
        assert (
            "cloze" not in correction_prompt.lower()
            or "multiple_choice" in correction_prompt
        )

    async def test_generate_quiz_raises_after_max_retries(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
    ):
        """Test that ValueError is raised after max retries."""
        mock_provider.call.return_value = invalid_quiz_json

        with pytest.raises(ValueError) as exc_info:
            await service.generate_quiz(generation_spec, max_retries=2)

        assert "ungültiges Datenformat" in str(exc_info.value)
        # Initial attempt + 2 retries = 3 calls
        assert mock_provider.call.call_count == 3

    async def test_generate_quiz_respects_max_retries_parameter(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
    ):
        """Test that max_retries parameter is respected."""
        mock_provider.call.return_value = invalid_quiz_json

        with pytest.raises(ValueError):
            await service.generate_quiz(generation_spec, max_retries=1)

        # Initial attempt + 1 retry = 2 calls
        assert mock_provider.call.call_count == 2

    async def test_generate_quiz_zero_retries(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
    ):
        """Test that zero retries means no retry attempts."""
        mock_provider.call.return_value = invalid_quiz_json

        with pytest.raises(ValueError):
            await service.generate_quiz(generation_spec, max_retries=0)

        # Only initial attempt, no retries
        assert mock_provider.call.call_count == 1

    async def test_generate_quiz_succeeds_on_second_retry(
        self,
        service,
        mock_provider,
        generation_spec,
        invalid_quiz_json,
        valid_quiz_json,
    ):
        """Test that generate_quiz can succeed on second retry."""
        mock_provider.call.side_effect = [
            invalid_quiz_json,
            invalid_quiz_json,
            valid_quiz_json,
        ]

        result = await service.generate_quiz(generation_spec, max_retries=2)

        assert result.title == "Test Quiz"
        assert mock_provider.call.call_count == 3


class TestLLMServiceCallLlmApi:
    """Tests for LLMService provider call method."""

    @pytest.fixture
    def mock_provider(self):
        """Mock LLM provider."""
        provider = AsyncMock()
        provider.call = AsyncMock()
        provider.health_check = AsyncMock(return_value={"status": "ok"})
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        """Create LLMService instance with mocked provider."""
        return LLMService(provider=mock_provider)

    async def test_call_llm_api_includes_system_prompt(
        self,
        service,
        mock_provider,
    ):
        """Test that provider.call receives messages including system prompt."""
        mock_provider.call.return_value = "{}"

        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

        await mock_provider.call(messages, ModelRole.GENERATION)

        mock_provider.call.assert_called_once()
        call_args = mock_provider.call.call_args
        passed_messages = call_args[0][0]
        assert passed_messages[0]["role"] == "system"
        assert passed_messages[0]["content"] == "System prompt"
        assert passed_messages[1]["role"] == "user"
        assert passed_messages[1]["content"] == "User message"

    async def test_call_llm_api_preserves_message_order(
        self,
        service,
        mock_provider,
    ):
        """Test that provider.call preserves message order."""
        mock_provider.call.return_value = "{}"

        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]

        await mock_provider.call(messages, ModelRole.GENERATION)

        mock_provider.call.assert_called_once()
        call_args = mock_provider.call.call_args
        passed_messages = call_args[0][0]
        assert len(passed_messages) == 4
        assert passed_messages[0]["content"] == "System"
        assert passed_messages[1]["content"] == "First"
        assert passed_messages[2]["content"] == "Second"
        assert passed_messages[3]["content"] == "Third"
