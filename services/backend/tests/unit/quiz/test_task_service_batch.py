"""Tests for TaskService.get_tasks_batch business logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.quiz.services.task_service import TaskService
from app.modules.quiz.exceptions import AccessDeniedException


pytestmark = pytest.mark.unit


class TestTaskServiceGetTasksBatch:
    """Tests for TaskService.get_tasks_batch method."""

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
        return AsyncMock()

    @pytest.fixture
    def mock_mapping_registry(self):
        registry = MagicMock()
        # Make .get(type).to_dto(task) return a sentinel per task
        strategy = MagicMock()
        strategy.to_dto.side_effect = lambda t: f"dto-{t.task_id}"
        registry.get.return_value = strategy
        return registry

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
    def user_id(self):
        return uuid.uuid4()

    async def test_returns_empty_list_for_empty_input(
        self,
        service,
        mock_task_repo,
        user_id,
    ):
        mock_task_repo.get_by_ids.return_value = []

        result = await service.get_tasks_batch([], user_id)

        assert result == []
        mock_task_repo.get_by_ids.assert_called_once_with([])

    async def test_returns_dtos_for_accessible_tasks(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        user_id,
    ):
        quiz_id = uuid.uuid4()
        task1 = MagicMock()
        task1.task_id = uuid.uuid4()
        task1.quiz_id = quiz_id
        task1.type = "free_text"
        task2 = MagicMock()
        task2.task_id = uuid.uuid4()
        task2.quiz_id = quiz_id
        task2.type = "multiple_choice"

        mock_task_repo.get_by_ids.return_value = [task1, task2]
        mock_ownership_repo.user_has_access.return_value = True

        result = await service.get_tasks_batch(
            [task1.task_id, task2.task_id],
            user_id,
        )

        assert len(result) == 2
        # Access check called once per unique quiz_id
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
        )

    async def test_checks_access_per_unique_quiz(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        user_id,
    ):
        quiz_id_a = uuid.uuid4()
        quiz_id_b = uuid.uuid4()
        task1 = MagicMock()
        task1.task_id = uuid.uuid4()
        task1.quiz_id = quiz_id_a
        task1.type = "free_text"
        task2 = MagicMock()
        task2.task_id = uuid.uuid4()
        task2.quiz_id = quiz_id_b
        task2.type = "free_text"

        mock_task_repo.get_by_ids.return_value = [task1, task2]
        mock_ownership_repo.user_has_access.return_value = True

        await service.get_tasks_batch(
            [task1.task_id, task2.task_id],
            user_id,
        )

        assert mock_ownership_repo.user_has_access.call_count == 2

    async def test_raises_access_denied_when_no_access(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        user_id,
    ):
        quiz_id = uuid.uuid4()
        task = MagicMock()
        task.task_id = uuid.uuid4()
        task.quiz_id = quiz_id
        task.type = "free_text"

        mock_task_repo.get_by_ids.return_value = [task]
        mock_ownership_repo.user_has_access.return_value = False

        with pytest.raises(AccessDeniedException):
            await service.get_tasks_batch([task.task_id], user_id)

    async def test_raises_access_denied_when_partial_access(
        self,
        service,
        mock_task_repo,
        mock_ownership_repo,
        user_id,
    ):
        """If user has access to one quiz but not another, raises AccessDeniedException."""
        quiz_id_ok = uuid.uuid4()
        quiz_id_denied = uuid.uuid4()
        task1 = MagicMock()
        task1.task_id = uuid.uuid4()
        task1.quiz_id = quiz_id_ok
        task1.type = "free_text"
        task2 = MagicMock()
        task2.task_id = uuid.uuid4()
        task2.quiz_id = quiz_id_denied
        task2.type = "free_text"

        mock_task_repo.get_by_ids.return_value = [task1, task2]

        async def _access_check(quiz_id, user_id):
            return quiz_id == quiz_id_ok

        mock_ownership_repo.user_has_access.side_effect = _access_check

        with pytest.raises(AccessDeniedException):
            await service.get_tasks_batch(
                [task1.task_id, task2.task_id],
                user_id,
            )
