"""Quiz model to DTO mappings."""

from app.modules.quiz.models.quiz import Quiz
from app.modules.quiz.models.quiz_ownership import OwnershipRole
from app.modules.quiz.models.task import TaskType
from app.modules.quiz.schemas.quiz_output import QuizDetailDto, QuizSummaryDto
from app.modules.quiz.schemas import TaskDetailDto


def quiz_to_list_item(
    quiz: Quiz,
    role: OwnershipRole,
    question_count: int = 0,
    question_types: list[TaskType] | None = None,
) -> QuizSummaryDto:
    """Convert Quiz model to QuizSummaryDto.

    Args:
        quiz: Quiz model instance
        role: User's ownership role for this quiz

    Returns:
        QuizSummaryDto with quiz summary and role
    """
    return QuizSummaryDto(
        quiz_id=quiz.quiz_id,
        title=quiz.title,
        topic=quiz.topic,
        state=quiz.state,
        status=quiz.status,
        role=role,
        created_at=quiz.created_at,
        question_count=question_count,
        question_types=question_types or [],
    )


def quiz_to_detail_response(quiz: Quiz, tasks: list[TaskDetailDto]) -> QuizDetailDto:
    """Convert Quiz model to QuizDetailDto.

    Args:
        quiz: Quiz model instance
        tasks: List of TaskDetailDtos belonging to this quiz

    Returns:
        QuizDetailDto with full quiz details and tasks
    """
    return QuizDetailDto(
        quiz_id=quiz.quiz_id,
        title=quiz.title,
        topic=quiz.topic,
        state=quiz.state,
        status=quiz.status,
        created_at=quiz.created_at,
        created_by=quiz.created_by,
        tasks=tasks,
    )
