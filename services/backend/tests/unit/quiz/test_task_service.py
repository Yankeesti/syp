"""Tests for TaskService business logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.quiz.services.task_service import TaskService
from app.modules.quiz.models import OwnershipRole
from app.modules.quiz.exceptions import (
    TaskNotFoundException,
    AccessDeniedException,
)


pytestmark = pytest.mark.unit


class TestTaskServiceDeleteTask:
    """Tests for TaskService.delete_task method."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ownership_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_edit_session_service(self):
        service = AsyncMock()
        session = MagicMock()
        session.draft_version_id = uuid.uuid4()
        service.require_active_session.return_value = session
        return service

    @pytest.fixture
    def mock_mapping_registry(self):
        return MagicMock()

    @pytest.fixture
    def mock_update_registry(self):
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_db,
        mock_task_repo,
        mock_ownership_repo,
        mock_edit_session_service,
        mock_mapping_registry,
        mock_update_registry,
    ):
        return TaskService(
            mock_db,
            mock_task_repo,
            mock_ownership_repo,
            mock_edit_session_service,
            mock_mapping_registry,
            mock_update_registry,
        )

    @pytest.fixture
    def task_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def quiz_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def edit_session_id(self):
        return uuid.uuid4()

    async def test_delete_task_raises_not_found(
        self,
        service,
        mock_task_repo,
        task_id,
        user_id,
        edit_session_id,
    ):
        mock_task_repo.get_by_id.return_value = None

        with pytest.raises(TaskNotFoundException):
            await service.delete_task(task_id, user_id, edit_session_id)

        mock_task_repo.get_by_id.assert_called_once_with(task_id)

    async def test_delete_task_raises_access_denied(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        mock_edit_session_service,
        task_id,
        quiz_id,
        user_id,
        edit_session_id,
    ):
        mock_task = MagicMock()
        mock_task.quiz_id = quiz_id
        mock_task.quiz_version_id = (
            mock_edit_session_service.require_active_session.return_value.draft_version_id
        )
        mock_task_repo.get_by_id.return_value = mock_task
        mock_ownership_repo.user_has_access.return_value = False

        with pytest.raises(AccessDeniedException) as exc_info:
            await service.delete_task(task_id, user_id, edit_session_id)

        assert (
            exc_info.value.message == "You do not have permission to delete this task"
        )
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
            required_role=OwnershipRole.EDITOR,
        )

    async def test_delete_task_success(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        mock_edit_session_service,
        mock_db,
        task_id,
        quiz_id,
        user_id,
        edit_session_id,
    ):
        mock_task = MagicMock()
        mock_task.quiz_id = quiz_id
        mock_task.quiz_version_id = (
            mock_edit_session_service.require_active_session.return_value.draft_version_id
        )
        mock_task_repo.get_by_id.return_value = mock_task
        mock_ownership_repo.user_has_access.return_value = True
        mock_task_repo.delete.return_value = True

        await service.delete_task(task_id, user_id, edit_session_id)

        mock_task_repo.delete.assert_called_once_with(task_id)

    async def test_delete_task_commits_transaction(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        mock_edit_session_service,
        mock_db,
        task_id,
        quiz_id,
        user_id,
        edit_session_id,
    ):
        mock_task = MagicMock()
        mock_task.quiz_id = quiz_id
        mock_task.quiz_version_id = (
            mock_edit_session_service.require_active_session.return_value.draft_version_id
        )
        mock_task_repo.get_by_id.return_value = mock_task
        mock_ownership_repo.user_has_access.return_value = True

        await service.delete_task(task_id, user_id, edit_session_id)

        mock_db.commit.assert_called_once()
