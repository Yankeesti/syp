"""Tests for learning module exceptions."""

import pytest

from app.modules.learning.exceptions import (
    LearningModuleException,
    AttemptNotFoundException,
    AttemptLockedException,
    QuizNotFoundException,
    QuizNotCompletedException,
    AccessDeniedException,
    TaskNotFoundException,
    AnswerTypeMismatchException,
    AnswerNotFoundException,
    InvalidAnswerTypeException,
)


class TestLearningExceptions:
    """Tests for learning module exceptions."""

    def test_attempt_not_found_message(self):
        """Test AttemptNotFoundException message."""
        exc = AttemptNotFoundException("abc-123")
        assert "abc-123" in str(exc)
        assert exc.attempt_id == "abc-123"

    def test_attempt_locked_message(self):
        """Test AttemptLockedException message."""
        exc = AttemptLockedException("xyz-789")
        assert "xyz-789" in str(exc)
        assert "locked" in str(exc).lower()

    def test_quiz_not_found_message(self):
        """Test QuizNotFoundException message."""
        exc = QuizNotFoundException("quiz-id")
        assert "quiz-id" in str(exc)

    def test_quiz_not_completed_message(self):
        """Test QuizNotCompletedException message."""
        exc = QuizNotCompletedException("quiz-id")
        assert "quiz-id" in str(exc)
        assert "completed" in str(exc).lower()

    def test_access_denied_default_message(self):
        """Test AccessDeniedException default message."""
        exc = AccessDeniedException()
        assert "denied" in str(exc).lower()

    def test_access_denied_custom_message(self):
        """Test AccessDeniedException custom message."""
        exc = AccessDeniedException("Custom access error")
        assert "Custom access error" in str(exc)

    def test_task_not_found_message(self):
        """Test TaskNotFoundException message."""
        exc = TaskNotFoundException("task-123")
        assert "task-123" in str(exc)

    def test_answer_type_mismatch_message(self):
        """Test AnswerTypeMismatchException message."""
        exc = AnswerTypeMismatchException("multiple_choice", "free_text")
        assert "multiple_choice" in str(exc)
        assert "free_text" in str(exc)
        assert exc.expected == "multiple_choice"
        assert exc.got == "free_text"

    def test_answer_not_found_message(self):
        """Test AnswerNotFoundException message."""
        exc = AnswerNotFoundException("task-456")
        assert "task-456" in str(exc)

    def test_invalid_answer_type_message(self):
        """Test InvalidAnswerTypeException message."""
        exc = InvalidAnswerTypeException("free_text", "multiple_choice")
        assert "free_text" in str(exc)
        assert "multiple_choice" in str(exc)
        assert exc.expected == "free_text"
        assert exc.actual == "multiple_choice"

    def test_all_inherit_from_base(self):
        """Test that all exceptions inherit from LearningModuleException."""
        exceptions = [
            AttemptNotFoundException("id"),
            AttemptLockedException("id"),
            QuizNotFoundException("id"),
            QuizNotCompletedException("id"),
            AccessDeniedException(),
            TaskNotFoundException("id"),
            AnswerTypeMismatchException("a", "b"),
            AnswerNotFoundException("id"),
            InvalidAnswerTypeException("a", "b"),
        ]

        for exc in exceptions:
            assert isinstance(exc, LearningModuleException)
            assert isinstance(exc, Exception)
