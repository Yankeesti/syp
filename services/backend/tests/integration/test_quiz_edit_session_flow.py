import pytest
from uuid import UUID
from sqlalchemy import func, select

import app.core.database as database
from app.modules.quiz.models import QuizEditSession, QuizVersion, Task
from app.modules.quiz.models.quiz_edit_session import QuizEditSessionStatus
from app.modules.quiz.models.quiz_version import QuizVersionStatus

pytestmark = pytest.mark.integration


async def _create_quiz_and_tasks(authed_client):
    create = await authed_client.post(
        "/quiz/quizzes",
        data={"user_description": "Testing"},
    )
    assert create.status_code == 202
    quiz_id = UUID(create.json()["quiz_id"])

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    tasks = detail.json()["tasks"]
    assert tasks
    return quiz_id, tasks


async def _start_edit_session(authed_client, quiz_id):
    resp = await authed_client.post(f"/quiz/quizzes/{quiz_id}/edit/start")
    assert resp.status_code == 201
    payload = resp.json()
    return UUID(payload["edit_session_id"]), payload["quiz"]["tasks"]


def _task_by_type(tasks, task_type):
    for task in tasks:
        if task["type"] == task_type:
            return task
    raise AssertionError(f"Task type {task_type} not found")


async def test_start_edit_creates_draft_with_new_task_ids(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    original_ids = {task["task_id"] for task in tasks}

    edit_session_id, draft_tasks = await _start_edit_session(authed_client, quiz_id)

    assert edit_session_id
    assert draft_tasks
    draft_ids = {task["task_id"] for task in draft_tasks}
    assert draft_ids.isdisjoint(original_ids)

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    current_ids = {task["task_id"] for task in detail.json()["tasks"]}
    assert current_ids == original_ids

    async with database.sessionmanager.session() as db:
        current_version_id = (
            await db.execute(
                select(QuizVersion.quiz_version_id).where(
                    QuizVersion.quiz_id == quiz_id,
                    QuizVersion.is_current.is_(True),
                ),
            )
        ).scalar_one()
        session_row = (
            await db.execute(
                select(QuizEditSession).where(
                    QuizEditSession.edit_session_id == edit_session_id,
                ),
            )
        ).scalar_one()
        draft_version = (
            await db.execute(
                select(QuizVersion).where(
                    QuizVersion.quiz_version_id == session_row.draft_version_id,
                ),
            )
        ).scalar_one()

    assert session_row.status == QuizEditSessionStatus.ACTIVE
    assert draft_version.status == QuizVersionStatus.DRAFT
    assert draft_version.is_current is False
    assert current_version_id != draft_version.quiz_version_id


async def test_commit_publishes_draft_changes(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    edit_session_id, draft_tasks = await _start_edit_session(authed_client, quiz_id)
    task = _task_by_type(draft_tasks, "free_text")

    payload = {
        "type": "free_text",
        "prompt": "Neue Frage?",
        "topic_detail": "Updated topic",
        "reference_answer": "Neue Antwort",
    }

    update = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
        headers={"X-Edit-Session-Id": str(edit_session_id)},
    )
    assert update.status_code == 200

    commit = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/commit",
        json={"edit_session_id": str(edit_session_id)},
    )
    assert commit.status_code == 200
    assert commit.json()["version_number"] == 2

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    persisted = _task_by_type(detail.json()["tasks"], "free_text")
    assert persisted["prompt"] == payload["prompt"]

    async with database.sessionmanager.session() as db:
        current_version_id = (
            await db.execute(
                select(QuizVersion.quiz_version_id).where(
                    QuizVersion.quiz_id == quiz_id,
                    QuizVersion.is_current.is_(True),
                ),
            )
        ).scalar_one()
        session_row = (
            await db.execute(
                select(QuizEditSession).where(
                    QuizEditSession.edit_session_id == edit_session_id,
                ),
            )
        ).scalar_one()
        version_row = (
            await db.execute(
                select(QuizVersion).where(
                    QuizVersion.quiz_version_id == session_row.draft_version_id,
                ),
            )
        ).scalar_one()

    assert session_row.status == QuizEditSessionStatus.COMMITTED
    assert version_row.status == QuizVersionStatus.PUBLISHED
    assert version_row.version_number == 2
    assert version_row.is_current is True
    assert current_version_id == version_row.quiz_version_id


async def test_abort_discards_draft_changes(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    original = _task_by_type(tasks, "multiple_choice")
    edit_session_id, draft_tasks = await _start_edit_session(authed_client, quiz_id)
    task = _task_by_type(draft_tasks, "multiple_choice")

    payload = {
        "type": "multiple_choice",
        "prompt": "Nicht speichern",
        "topic_detail": "Updated topic",
        "options": [
            {"text": "A", "is_correct": True, "explanation": None},
            {"text": "B", "is_correct": False, "explanation": None},
        ],
    }

    update = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
        headers={"X-Edit-Session-Id": str(edit_session_id)},
    )
    assert update.status_code == 200

    async with database.sessionmanager.session() as db:
        draft_version_id = (
            await db.execute(
                select(QuizEditSession.draft_version_id).where(
                    QuizEditSession.edit_session_id == edit_session_id,
                ),
            )
        ).scalar_one()

    abort = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/abort",
        json={"edit_session_id": str(edit_session_id)},
    )
    assert abort.status_code == 204

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    persisted = _task_by_type(detail.json()["tasks"], "multiple_choice")
    assert persisted["prompt"] == original["prompt"]

    async with database.sessionmanager.session() as db:
        session_row = (
            await db.execute(
                select(QuizEditSession).where(
                    QuizEditSession.edit_session_id == edit_session_id,
                ),
            )
        ).scalar_one_or_none()
        draft_count = (
            await db.execute(
                select(func.count(QuizVersion.quiz_version_id)).where(
                    QuizVersion.quiz_version_id == draft_version_id,
                ),
            )
        ).scalar_one()
        task_count = (
            await db.execute(
                select(func.count(Task.task_id)).where(
                    Task.quiz_version_id == draft_version_id,
                ),
            )
        ).scalar_one()

    assert session_row is None
    assert draft_count == 0
    assert task_count == 0


async def test_start_edit_aborts_existing_session(authed_client, mock_llm):
    quiz_id, _ = await _create_quiz_and_tasks(authed_client)
    first_session_id, _ = await _start_edit_session(authed_client, quiz_id)
    async with database.sessionmanager.session() as db:
        first_draft_version_id = (
            await db.execute(
                select(QuizEditSession.draft_version_id).where(
                    QuizEditSession.edit_session_id == first_session_id,
                ),
            )
        ).scalar_one()

    second = await authed_client.post(f"/quiz/quizzes/{quiz_id}/edit/start")
    assert second.status_code == 201
    second_session_id = UUID(second.json()["edit_session_id"])

    async with database.sessionmanager.session() as db:
        first_session = (
            await db.execute(
                select(QuizEditSession).where(
                    QuizEditSession.edit_session_id == first_session_id,
                ),
            )
        ).scalar_one_or_none()
        second_session = (
            await db.execute(
                select(QuizEditSession).where(
                    QuizEditSession.edit_session_id == second_session_id,
                ),
            )
        ).scalar_one()
        active_count = (
            await db.execute(
                select(func.count(QuizEditSession.edit_session_id)).where(
                    QuizEditSession.quiz_id == quiz_id,
                    QuizEditSession.status == QuizEditSessionStatus.ACTIVE,
                ),
            )
        ).scalar_one()
        draft_count = (
            await db.execute(
                select(func.count(QuizVersion.quiz_version_id)).where(
                    QuizVersion.quiz_version_id == first_draft_version_id,
                ),
            )
        ).scalar_one()
        task_count = (
            await db.execute(
                select(func.count(Task.task_id)).where(
                    Task.quiz_version_id == first_draft_version_id,
                ),
            )
        ).scalar_one()

    assert active_count == 1
    assert first_session is None
    assert second_session.status == QuizEditSessionStatus.ACTIVE
    assert draft_count == 0
    assert task_count == 0


async def test_update_requires_edit_session_header(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    _, draft_tasks = await _start_edit_session(authed_client, quiz_id)
    task = _task_by_type(draft_tasks, "free_text")

    payload = {
        "type": "free_text",
        "prompt": "Ohne Header",
        "topic_detail": "Updated topic",
        "reference_answer": "Antwort",
    }

    update = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
    )
    assert update.status_code == 400
