"""Learning module router - Attempts, Answers, and Evaluation endpoints."""

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from app.shared.dependencies import CurrentUserId
from app.modules.learning.dependencies import (
    AttemptAnswerServiceDep,
    EvaluationServiceDep,
)
from app.modules.learning.schemas import (
    AttemptListItem,
    AttemptDetailResponse,
    AttemptSummaryResponse,
    AnswerUpsertRequest,
    AnswerSavedResponse,
    FreeTextCorrectnessRequest,
    EvaluationResponse,
)
from app.modules.learning.schemas.attempt import AttemptLinks
from app.modules.learning.models.attempt import AttemptStatus

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=AttemptSummaryResponse,
    responses={
        200: {"description": "Resumed existing in_progress attempt"},
        201: {"description": "Created new attempt"},
        403: {"description": "Access denied"},
        404: {"description": "Quiz not found"},
        409: {"description": "Quiz not in completed status"},
    },
)
async def start_or_resume_attempt(
    quiz_id: UUID,
    user_id: CurrentUserId,
    service: AttemptAnswerServiceDep,
    response: Response,
) -> AttemptSummaryResponse:
    """
    Start a new attempt or resume an existing in_progress attempt.

    Returns 201 for new attempts, 200 for resumed attempts.
    """
    result, is_new = await service.start_or_resume_attempt(user_id, quiz_id)
    if is_new:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/attempts",
    response_model=list[AttemptListItem],
    responses={
        200: {"description": "List of attempts"},
    },
)
async def list_attempts(
    user_id: CurrentUserId,
    service: AttemptAnswerServiceDep,
    quiz_id: UUID | None = Query(default=None, description="Filter by quiz ID"),
    status: AttemptStatus | None = Query(default=None, description="Filter by status"),
) -> list[AttemptListItem]:
    """
    Get all attempts for the current user.

    Optional filters:
    - quiz_id: Filter by specific quiz
    - status: Filter by attempt status (in_progress, evaluated)

    Returns attempts ordered by started_at descending (newest first).
    """
    return await service.list_attempts(user_id, quiz_id, status)


@router.get(
    "/attempts/{attempt_id}",
    response_model=AttemptDetailResponse,
    responses={
        200: {"description": "Attempt with answers"},
        403: {"description": "Access denied"},
        404: {"description": "Attempt not found"},
    },
)
async def get_attempt(
    attempt_id: UUID,
    user_id: CurrentUserId,
    service: AttemptAnswerServiceDep,
    request: Request,
) -> AttemptDetailResponse:
    """Get a single attempt with its answers."""
    result = await service.get_attempt_with_answers(user_id, attempt_id)

    # Construct HAL-links
    if result.answers:
        task_ids = [a.task_id for a in result.answers]
        base_url = request.url_for("get_tasks_batch")
        query_string = urlencode([("task_id", str(tid)) for tid in task_ids])
        result.links = AttemptLinks(tasks=f"{base_url}?{query_string}")

    return result


@router.put(
    "/attempts/{attempt_id}/answers/{task_id}",
    response_model=AnswerSavedResponse,
    responses={
        200: {"description": "Answer saved successfully"},
        400: {"description": "Invalid answer type"},
        403: {"description": "Access denied"},
        404: {"description": "Attempt or task not found"},
        409: {"description": "Attempt is locked (already evaluated)"},
    },
)
async def save_answer(
    attempt_id: UUID,
    task_id: UUID,
    payload: AnswerUpsertRequest,
    user_id: CurrentUserId,
    service: AttemptAnswerServiceDep,
) -> AnswerSavedResponse:
    """
    Save or update an answer for a task (idempotent upsert).

    Supports auto-save functionality.
    """
    return await service.save_answer(user_id, attempt_id, task_id, payload)


@router.patch(
    "/attempts/{attempt_id}/answers/{task_id}/free-text-correctness",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Correctness set successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Attempt or answer not found"},
        409: {"description": "Attempt is locked (already evaluated)"},
        422: {"description": "Answer is not a free text answer"},
    },
)
async def set_free_text_correctness(
    attempt_id: UUID,
    task_id: UUID,
    payload: FreeTextCorrectnessRequest,
    user_id: CurrentUserId,
    service: AttemptAnswerServiceDep,
) -> None:
    """
    Set self-evaluation correctness for a free text answer.

    Sets percentage_correct to 100% if is_correct=true, 0% otherwise.
    """
    await service.set_free_text_correctness(
        user_id,
        attempt_id,
        task_id,
        payload.is_correct,
    )


@router.post(
    "/attempts/{attempt_id}/evaluation",
    response_model=EvaluationResponse,
    responses={
        200: {"description": "Evaluation completed successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Attempt not found"},
        409: {"description": "Attempt is locked (already evaluated)"},
    },
)
async def evaluate_attempt(
    attempt_id: UUID,
    user_id: CurrentUserId,
    service: EvaluationServiceDep,
) -> EvaluationResponse:
    """
    Evaluate all answers and lock the attempt.

    - Calculates percentage_correct for each answer
    - Calculates total_percentage for the attempt
    - Sets attempt status to 'evaluated'
    """
    return await service.evaluate_attempt(user_id, attempt_id)


# Health check endpoints (keep for compatibility)
@router.get("/health", tags=["health"])
async def learning_health() -> dict:
    """Health check for learning module."""
    return {"status": "healthy", "module": "learning"}
