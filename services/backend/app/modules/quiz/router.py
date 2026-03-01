"""Quiz and Task API endpoints."""

from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, status
from pypdf import PdfReader

from app.shared.dependencies import CurrentUserId, DBSessionDep
from app.modules.quiz.models import OwnershipRole
from app.modules.quiz.models.task import TaskType
from app.modules.quiz.dependencies import (
    QuizServiceDep,
    TaskServiceDep,
    ShareLinkServiceDep,
    QuizEditSessionServiceDep,
)
from app.modules.quiz.schemas import (
    QuizCreateRequest,
    QuizSummaryDto,
    QuizCreationStatus,
    QuizDetailDto,
    QuizGenerationSpec,
    TaskDetailDto,
    TaskUpdateDto,
    MultipleChoiceTaskResponse,
    FreeTextTaskResponse,
    ClozeTaskResponse,
    ShareLinkCreateRequest,
    ShareLinkDto,
    ShareLinkInfoDto,
    QuizEditSessionStartResponse,
    QuizEditSessionCommitRequest,
    QuizEditSessionCommitResponse,
    QuizEditSessionAbortRequest,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get(
    "/quizzes",
    response_model=list[QuizSummaryDto],
    status_code=status.HTTP_200_OK,
)
async def list_quizzes(
    quiz_service: QuizServiceDep,
    user_id: CurrentUserId,
    roles: Annotated[
        list[OwnershipRole] | None,
        Query(
            description="Filter by ownership roles. If not provided, returns quizzes for all roles.",
        ),
    ] = None,
):
    """
    List all quizzes where the current user has ownership.

    Returns quizzes where the user is owner, editor, or viewer.
    Use the `roles` query parameter to filter by specific ownership roles.

    Examples:
    - GET /quizzes - Returns all quizzes where user has any role
    - GET /quizzes?roles=owner - Returns only quizzes where user is owner
    - GET /quizzes?roles=owner&roles=editor - Returns quizzes where user is owner or editor
    """
    return await quiz_service.list_user_quizzes(user_id, roles)


@router.post(
    "/quizzes",
    response_model=QuizCreationStatus,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_quiz(
    background_tasks: BackgroundTasks,
    quiz_service: QuizServiceDep,
    user_id: CurrentUserId,
    request: Annotated[QuizCreateRequest, Depends(QuizCreateRequest.as_form)],
    types: Annotated[
        list[TaskType] | None,
        Query(
            description="Task types to generate. If not provided, all types are generated.",
        ),
    ] = None,
):
    """
    Create a new quiz and start async task generation.

    Accepts either a file upload or user_description (or both).
    Task types can be specified via query parameters (e.g., ?types=multiple_choice&types=free_text).
    If no types are specified, all task types will be generated.

    The quiz is created with status="pending". A background task will:
    1. Update status to "generating"
    2. Call LLM service to generate all tasks at once
    3. Persist generated tasks
    4. Update status to "completed" (or "failed" on error)

    Frontend should poll GET /quizzes/{quiz_id} to check generation status.

    Returns 202 Accepted with quiz_id and status.
    """
    # Read file bytes while request is still active (UploadFile closes after request)
    if request.file:
        file_bytes = await request.file.read()
        reader = PdfReader(BytesIO(file_bytes))
        file_text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
        file_content = file_text.encode("utf-8")
    else:
        file_content = None

    # Default to all task types if none specified
    task_types = types if types else list(TaskType)

    # Convert API request to internal generation input
    generation_input = QuizGenerationSpec(
        task_types=task_types,
        user_description=request.user_description,
        file_content=file_content,
    )

    return await quiz_service.create_quiz(
        background_tasks=background_tasks,
        user_id=user_id,
        generation_input=generation_input,
    )


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizDetailDto,
    status_code=status.HTTP_200_OK,
)
async def get_quiz(
    quiz_id: UUID,
    quiz_service: QuizServiceDep,
    user_id: CurrentUserId,
):
    """
    Get detailed quiz information including all tasks.

    Requires user to have access to the quiz (owner/shared or public).
    """
    return await quiz_service.get_quiz_detail(quiz_id, user_id)


@router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    quiz_service: QuizServiceDep,
    user_id: CurrentUserId,
):
    """
    Delete a quiz.

    Only the quiz owner can delete the quiz.
    Cascades to all tasks and ownership records.
    """
    await quiz_service.delete_quiz(quiz_id, user_id)
    return None


@router.get(
    "/tasks",
    response_model=list[
        MultipleChoiceTaskResponse | FreeTextTaskResponse | ClozeTaskResponse
    ],
    status_code=status.HTTP_200_OK,
)
async def get_tasks_batch(
    task_service: TaskServiceDep,
    user_id: CurrentUserId,
    task_id: Annotated[
        list[UUID] | None,
        Query(description="Task IDs to load"),
    ] = None,
):
    """
    Load multiple tasks by ID (batch).

    Accepts one or more task_id query parameters.
    Example: GET /quiz/tasks?task_id=abc&task_id=def
    """
    return await task_service.get_tasks_batch(task_id or [], user_id)


@router.put(
    "/tasks/{task_id}",
    response_model=TaskDetailDto,
    status_code=status.HTTP_200_OK,
)
async def update_task(
    task_id: UUID,
    update_dto: TaskUpdateDto,
    task_service: TaskServiceDep,
    user_id: CurrentUserId,
    edit_session_id: Annotated[
        UUID | None,
        Header(alias="X-Edit-Session-Id"),
    ] = None,
):
    """
    Update a task.

    Requires EDITOR or OWNER role on the quiz.

    The request body must include the task type, which must match the
    existing task's type. All other fields are optional for partial updates.

    For Multiple Choice tasks: if 'options' is provided, all existing options
    are replaced (Replace-All semantics).

    For Cloze tasks: if 'blanks' is provided, all existing blanks are replaced
    (Replace-All semantics).
    """
    return await task_service.update_task(
        task_id,
        user_id,
        update_dto,
        edit_session_id,
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    task_service: TaskServiceDep,
    user_id: CurrentUserId,
    edit_session_id: Annotated[
        UUID | None,
        Header(alias="X-Edit-Session-Id"),
    ] = None,
):
    """
    Delete a task from a quiz.

    Requires EDITOR or OWNER role on the quiz.
    Cascades to all nested entities (options, blanks).
    """
    await task_service.delete_task(task_id, user_id, edit_session_id)
    return None


@router.post(
    "/quizzes/{quiz_id}/edit/start",
    response_model=QuizEditSessionStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_quiz_edit(
    quiz_id: UUID,
    edit_session_service: QuizEditSessionServiceDep,
    user_id: CurrentUserId,
):
    """
    Start an edit session for a quiz.

    Creates a draft version and returns the draft quiz details plus session id.
    Only one active session per quiz is allowed.
    """
    return await edit_session_service.start_edit(quiz_id, user_id)


@router.post(
    "/quizzes/{quiz_id}/edit/commit",
    response_model=QuizEditSessionCommitResponse,
    status_code=status.HTTP_200_OK,
)
async def commit_quiz_edit(
    quiz_id: UUID,
    request: QuizEditSessionCommitRequest,
    edit_session_service: QuizEditSessionServiceDep,
    user_id: CurrentUserId,
):
    """
    Commit an active edit session.

    Publishes the draft version and marks it as the current version.
    """
    return await edit_session_service.commit_edit(
        quiz_id,
        user_id,
        request.edit_session_id,
    )


@router.post(
    "/quizzes/{quiz_id}/edit/abort",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def abort_quiz_edit(
    quiz_id: UUID,
    request: QuizEditSessionAbortRequest,
    edit_session_service: QuizEditSessionServiceDep,
    user_id: CurrentUserId,
):
    """
    Abort an active edit session and discard the draft version.
    """
    await edit_session_service.abort_edit(
        quiz_id,
        user_id,
        request.edit_session_id,
    )
    return None


@router.post(
    "/quizzes/{quiz_id}/share-links",
    response_model=ShareLinkDto,
    status_code=status.HTTP_201_CREATED,
)
async def create_share_link(
    quiz_id: UUID,
    request: ShareLinkCreateRequest,
    share_link_service: ShareLinkServiceDep,
    user_id: CurrentUserId,
):
    """
    Create a new share link for a quiz.

    Only OWNER or EDITOR can create share links.
    The link grants VIEWER access to the quiz.

    Optional parameters:
    - duration: Link validity duration. Accepts seconds (int/float) or ISO 8601 duration string
                (e.g., "P1D" for 1 day, "PT12H" for 12 hours). If null, the link never expires.
    - max_uses: Maximum number of uses (null = unlimited)

    Examples:
        {"duration": 86400, "max_uses": 10}  # 1 day in seconds
        {"duration": "P1DT12H", "max_uses": 5}  # ISO 8601: 1 day + 12 hours
        {"duration": null, "max_uses": 10}  # No expiration

    Returns the created link with a shareable URL pointing to the frontend.
    """
    return await share_link_service.create_share_link(
        quiz_id,
        user_id,
        request.duration,
        request.max_uses,
    )


@router.get(
    "/quizzes/{quiz_id}/share-links",
    response_model=list[ShareLinkDto],
    status_code=status.HTTP_200_OK,
)
async def list_share_links(
    quiz_id: UUID,
    share_link_service: ShareLinkServiceDep,
    user_id: CurrentUserId,
):
    """
    List all share links for a quiz.

    Only OWNER or EDITOR can view share links.
    Returns all links (active and revoked) with usage statistics.
    """
    return await share_link_service.get_share_links(quiz_id, user_id)


@router.delete(
    "/quizzes/{quiz_id}/share-links/{share_link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_share_link(
    quiz_id: UUID,
    share_link_id: UUID,
    share_link_service: ShareLinkServiceDep,
    user_id: CurrentUserId,
):
    """
    Revoke a share link.

    Only OWNER or EDITOR can revoke share links.
    Sets is_active = false, preventing future redemptions.
    """
    await share_link_service.revoke_share_link(share_link_id, user_id)
    return None


@router.get(
    "/share/{token}",
    response_model=ShareLinkInfoDto,
    status_code=status.HTTP_200_OK,
)
async def validate_share_link(
    token: str,
    share_link_service: ShareLinkServiceDep,
):
    """
    Validate a share link and get quiz information.

    This is a public endpoint (no authentication required).
    Used by the frontend to display quiz info before login/redemption.

    Returns quiz details if link is valid, or error information if invalid.
    """
    return await share_link_service.validate_share_link(token)


@router.post(
    "/share/{token}/redeem",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def redeem_share_link(
    token: str,
    share_link_service: ShareLinkServiceDep,
    user_id: CurrentUserId,
):
    """
    Redeem a share link to gain viewer access to a quiz.

    Requires authentication. The authenticated user will receive VIEWER role.

    Validation:
    - Link must be active (not revoked)
    - Link must not be expired
    - Link must not have reached max_uses
    - User must not already have access to the quiz

    On success, creates quiz_ownership record with role=viewer.
    """
    await share_link_service.redeem_share_link(token, user_id)
    return None
