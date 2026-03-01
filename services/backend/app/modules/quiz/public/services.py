"""Public service wrapper for quiz module access.

This service exposes a logic-free interface for other modules by delegating
to the internal QuizService methods.
"""

from uuid import UUID

from app.modules.quiz.services import QuizService
from app.modules.quiz.schemas import QuizAccessDto, TaskDetailDto


class QuizPublicService:
    """Thin public facade for quiz module operations."""

    def __init__(self, quiz_service: QuizService):
        """
        Initialize with QuizService dependency.

        Args:
            quiz_service: QuizService instance
        """
        self.quiz_service = quiz_service

    async def get_quiz_access(self, quiz_id: UUID, user_id: UUID) -> QuizAccessDto:
        """Get access-checked quiz metadata."""
        return await self.quiz_service.get_quiz_access(quiz_id, user_id)

    async def get_tasks(
        self,
        quiz_id: UUID,
        user_id: UUID,
    ) -> list[TaskDetailDto]:
        """Get access-checked tasks for a quiz."""
        return await self.quiz_service.get_tasks(quiz_id, user_id)

    async def get_task(self, task_id: UUID, user_id: UUID) -> TaskDetailDto:
        """Get access-checked task by ID."""
        return await self.quiz_service.get_task(task_id, user_id)
