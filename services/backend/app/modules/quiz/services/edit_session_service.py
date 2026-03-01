"""Quiz edit session service for staged updates."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.exceptions import (
    AccessDeniedException,
    EditSessionInactiveException,
    EditSessionNotFoundException,
    EditSessionTaskMismatchException,
)
from app.modules.quiz.models import (
    OwnershipRole,
    QuizEditSession,
    Task,
)
from app.modules.quiz.models.quiz_edit_session import QuizEditSessionStatus
from app.modules.quiz.repositories import (
    QuizRepository,
    QuizOwnershipRepository,
    TaskRepository,
    QuizVersionRepository,
    QuizEditSessionRepository,
)
from app.modules.quiz.schemas import QuizDetailDto, TaskDetailDto
from app.modules.quiz.schemas.edit_session import (
    QuizEditSessionCommitResponse,
    QuizEditSessionStartResponse,
)
from app.modules.quiz.strategies import (
    TaskCloneRegistry,
    TaskMappingRegistry,
    normalize_task_type,
)


class QuizEditSessionService:
    """Service for edit session lifecycle and draft commits."""

    def __init__(
        self,
        db: AsyncSession,
        quiz_repo: QuizRepository,
        ownership_repo: QuizOwnershipRepository,
        task_repo: TaskRepository,
        version_repo: QuizVersionRepository,
        session_repo: QuizEditSessionRepository,
        mapping_registry: TaskMappingRegistry,
        clone_registry: TaskCloneRegistry,
    ) -> None:
        self.db = db
        self.quiz_repo = quiz_repo
        self.ownership_repo = ownership_repo
        self.task_repo = task_repo
        self.version_repo = version_repo
        self.session_repo = session_repo
        self.task_mapping_registry = mapping_registry
        self.task_clone_registry = clone_registry

    async def start_edit(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> QuizEditSessionStartResponse:
        quiz = await self._require_quiz(quiz_id)
        await self._require_editor_access(
            quiz_id,
            user_id,
            "You do not have permission to edit this quiz",
        )

        active_session = await self.session_repo.get_active_for_quiz(quiz_id)
        if active_session:
            await self._delete_session_and_draft(active_session)

        current_version_id = await self.version_repo.get_current_version_id(quiz_id)
        if current_version_id is None:
            raise EditSessionNotFoundException("Quiz version not initialized")

        draft_version = await self.version_repo.create_draft(
            quiz_id=quiz_id,
            created_by=user_id,
            base_version_id=current_version_id,
        )

        draft_tasks = await self._clone_tasks(
            current_version_id,
            draft_version.quiz_version_id,
        )

        session = await self.session_repo.create(
            quiz_id=quiz_id,
            draft_version_id=draft_version.quiz_version_id,
            started_by=user_id,
        )

        await self.db.commit()

        task_dtos = [self._task_to_dto(task) for task in draft_tasks]

        return QuizEditSessionStartResponse(
            edit_session_id=session.edit_session_id,
            quiz=QuizDetailDto(
                quiz_id=quiz.quiz_id,
                title=quiz.title,
                topic=quiz.topic,
                status=quiz.status,
                state=quiz.state,
                created_by=quiz.created_by,
                created_at=quiz.created_at,
                tasks=task_dtos,
            ),
        )

    async def commit_edit(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        edit_session_id: uuid.UUID,
    ) -> QuizEditSessionCommitResponse:
        session = await self._require_active_session(edit_session_id, user_id, quiz_id)

        await self._require_editor_access(
            quiz_id,
            user_id,
            "You do not have permission to commit edits",
        )

        latest_version = await self.version_repo.get_latest_version_number(quiz_id)
        next_version_number = 1 if latest_version is None else latest_version + 1

        await self.version_repo.publish_version(
            session.draft_version_id,
            version_number=next_version_number,
        )
        await self.version_repo.set_current_version(quiz_id, session.draft_version_id)
        await self.session_repo.update_status(
            edit_session_id,
            status=QuizEditSessionStatus.COMMITTED,
        )

        await self.db.commit()

        return QuizEditSessionCommitResponse(
            quiz_id=quiz_id,
            current_version_id=session.draft_version_id,
            version_number=next_version_number,
        )

    async def abort_edit(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        edit_session_id: uuid.UUID,
    ) -> None:
        session = await self._require_active_session(edit_session_id, user_id, quiz_id)

        await self._require_editor_access(
            quiz_id,
            user_id,
            "You do not have permission to abort edits",
        )

        await self._delete_session_and_draft(session)

        await self.db.commit()

    async def require_active_session(
        self,
        edit_session_id: uuid.UUID,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID | None = None,
    ) -> "QuizEditSession":
        return await self._require_active_session(edit_session_id, user_id, quiz_id)

    async def ensure_task_in_session(
        self,
        task_id: uuid.UUID,
        edit_session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        session = await self._require_active_session(edit_session_id, user_id)
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            return
        if task.quiz_version_id != session.draft_version_id:
            raise EditSessionTaskMismatchException()

    async def _require_active_session(
        self,
        edit_session_id: uuid.UUID,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID | None = None,
    ) -> "QuizEditSession":
        session = await self.session_repo.get_by_id(edit_session_id)
        if session is None:
            raise EditSessionNotFoundException()

        if quiz_id is not None and session.quiz_id != quiz_id:
            raise EditSessionNotFoundException("Edit session does not match quiz")

        if session.started_by != user_id:
            raise AccessDeniedException("You do not own this edit session")

        if session.status != QuizEditSessionStatus.ACTIVE:
            raise EditSessionInactiveException("Edit session is not active")

        return session

    async def _require_quiz(self, quiz_id: uuid.UUID):
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise EditSessionNotFoundException("Quiz not found")
        return quiz

    async def _require_editor_access(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
    ) -> None:
        has_access = await self.ownership_repo.user_has_access(
            quiz_id=quiz_id,
            user_id=user_id,
            required_role=OwnershipRole.EDITOR,
        )
        if not has_access:
            raise AccessDeniedException(message)

    async def _delete_session_and_draft(self, session: QuizEditSession) -> None:
        draft_version_id = session.draft_version_id
        await self.session_repo.delete(session.edit_session_id)
        await self.version_repo.delete(draft_version_id)

    async def _clone_tasks(
        self,
        source_version_id: uuid.UUID,
        target_version_id: uuid.UUID,
    ) -> list[Task]:
        tasks = await self.task_repo.get_by_quiz_version(source_version_id)
        if not tasks:
            return []

        cloned_tasks = [
            self.task_clone_registry.get(normalize_task_type(task.type)).clone(
                task,
                target_version_id,
            )
            for task in tasks
        ]

        return await self.task_repo.save_many(cloned_tasks)

    def _task_to_dto(self, task) -> TaskDetailDto:
        task_type = normalize_task_type(task.type)
        return self.task_mapping_registry.get(task_type).to_dto(task)
