"""Tests for quiz module exceptions and exception handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.quiz.exceptions import (
    QuizModuleException,
    QuizNotFoundException,
    TaskNotFoundException,
    AccessDeniedException,
    InvalidTaskTypeException,
)
from app.modules.quiz.exception_handlers import register_exception_handlers


pytestmark = pytest.mark.unit


class TestQuizModuleExceptions:
    """Tests for domain exception classes."""

    def test_quiz_module_exception_stores_message(self):
        exc = QuizModuleException("Test message")
        assert exc.message == "Test message"
        assert str(exc) == "Test message"

    def test_quiz_not_found_exception_default_message(self):
        exc = QuizNotFoundException()
        assert exc.message == "Quiz not found"

    def test_quiz_not_found_exception_custom_message(self):
        exc = QuizNotFoundException("Custom quiz error")
        assert exc.message == "Custom quiz error"

    def test_task_not_found_exception_default_message(self):
        exc = TaskNotFoundException()
        assert exc.message == "Task not found"

    def test_task_not_found_exception_custom_message(self):
        exc = TaskNotFoundException("Custom task error")
        assert exc.message == "Custom task error"

    def test_access_denied_exception_default_message(self):
        exc = AccessDeniedException()
        assert exc.message == "Access denied"

    def test_access_denied_exception_custom_message(self):
        exc = AccessDeniedException("You shall not pass")
        assert exc.message == "You shall not pass"

    def test_invalid_task_type_exception_includes_type(self):
        exc = InvalidTaskTypeException("unknown_type")
        assert exc.message == "Invalid task type: unknown_type"
        assert exc.task_type == "unknown_type"

    def test_all_exceptions_inherit_from_base(self):
        assert issubclass(QuizNotFoundException, QuizModuleException)
        assert issubclass(TaskNotFoundException, QuizModuleException)
        assert issubclass(AccessDeniedException, QuizModuleException)
        assert issubclass(InvalidTaskTypeException, QuizModuleException)


class TestExceptionHandlers:
    """Tests for FastAPI exception handlers."""

    @pytest.fixture
    def app_with_handlers(self):
        """Create a FastAPI app with registered exception handlers."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/raise-quiz-not-found")
        async def raise_quiz_not_found():
            raise QuizNotFoundException()

        @app.get("/raise-quiz-not-found-custom")
        async def raise_quiz_not_found_custom():
            raise QuizNotFoundException("Quiz with ID xyz not found")

        @app.get("/raise-task-not-found")
        async def raise_task_not_found():
            raise TaskNotFoundException()

        @app.get("/raise-access-denied")
        async def raise_access_denied():
            raise AccessDeniedException()

        @app.get("/raise-access-denied-custom")
        async def raise_access_denied_custom():
            raise AccessDeniedException("Only owners can delete")

        @app.get("/raise-invalid-task-type")
        async def raise_invalid_task_type():
            raise InvalidTaskTypeException("bogus_type")

        return app

    @pytest.fixture
    def client(self, app_with_handlers):
        """Create a test client."""
        return TestClient(app_with_handlers)

    def test_quiz_not_found_returns_404(self, client):
        response = client.get("/raise-quiz-not-found")
        assert response.status_code == 404
        assert response.json() == {"detail": "Quiz not found"}

    def test_quiz_not_found_returns_404_with_custom_message(self, client):
        response = client.get("/raise-quiz-not-found-custom")
        assert response.status_code == 404
        assert response.json() == {"detail": "Quiz with ID xyz not found"}

    def test_task_not_found_returns_404(self, client):
        response = client.get("/raise-task-not-found")
        assert response.status_code == 404
        assert response.json() == {"detail": "Task not found"}

    def test_access_denied_returns_403(self, client):
        response = client.get("/raise-access-denied")
        assert response.status_code == 403
        assert response.json() == {"detail": "Access denied"}

    def test_access_denied_returns_403_with_custom_message(self, client):
        response = client.get("/raise-access-denied-custom")
        assert response.status_code == 403
        assert response.json() == {"detail": "Only owners can delete"}

    def test_invalid_task_type_returns_400(self, client):
        response = client.get("/raise-invalid-task-type")
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid task type: bogus_type"}
