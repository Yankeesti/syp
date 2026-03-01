"""Learning cleanup service for cross-module operations.

This module provides cleanup operations that are called from other modules.
Primary use case: Quiz module calls this when deleting quizzes to clean up
all related learning data (attempts and answers).
"""

from uuid import UUID

from app.modules.learning.repositories import AttemptRepository


class LearningCleanupService:
    """
    Thin wrapper service for cleanup operations called by other modules.

    This service is designed to be called from the Quiz module when a quiz
    is deleted, to clean up all related learning data (attempts and answers).
    """

    def __init__(self, attempt_repo: AttemptRepository) -> None:
        """
        Initialize cleanup service with repository.

        Args:
            attempt_repo: AttemptRepository instance
        """
        self.attempt_repo = attempt_repo

    async def delete_attempts_for_quiz(self, quiz_id: UUID) -> int:
        """
        Delete all attempts (and cascading answers) for a quiz.

        Called by Quiz module when a quiz is deleted.
        Returns the number of deleted attempts.

        Note: This method does NOT commit the transaction.
        The caller (Quiz service) is responsible for committing.

        Args:
            quiz_id: UUID of the quiz whose attempts should be deleted

        Returns:
            Count of deleted attempts (answers are cascaded automatically)
        """
        count = await self.attempt_repo.delete_by_quiz_id(quiz_id)
        return count
