"""Integration tests for GET /quiz/tasks batch endpoint and _links in AttemptDetailResponse.

Tests cover:
- Batch loading tasks by ID
- Authorization (owner, shared viewer, no access)
- Empty / missing query params
- _links.tasks in GET /learning/attempts/{attempt_id}
"""

import pytest

from tests.integration.helpers import build_answer_payload


pytestmark = pytest.mark.integration


async def _create_quiz_and_get_tasks(authed_client):
    """Create a quiz via LLM mock and return (quiz_id, tasks list)."""
    create = await authed_client.post(
        "/quiz/quizzes",
        data={"user_description": "Batch test"},
    )
    assert create.status_code == 202
    quiz_id = create.json()["quiz_id"]

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    tasks = detail.json()["tasks"]
    assert len(tasks) > 0
    return quiz_id, tasks


# ============================================================================
# Happy-path tests
# ============================================================================


async def test_batch_load_all_tasks(authed_client, mock_llm):
    """Owner can batch-load all tasks of their quiz."""
    quiz_id, tasks = await _create_quiz_and_get_tasks(authed_client)
    task_ids = [t["task_id"] for t in tasks]

    resp = await authed_client.get(
        "/quiz/tasks",
        params=[("task_id", tid) for tid in task_ids],
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == len(tasks)
    returned_ids = {t["task_id"] for t in data}
    assert returned_ids == set(task_ids)


async def test_batch_load_single_task(authed_client, mock_llm):
    """Batch endpoint works with a single task_id."""
    _, tasks = await _create_quiz_and_get_tasks(authed_client)
    single_id = tasks[0]["task_id"]

    resp = await authed_client.get(
        "/quiz/tasks",
        params={"task_id": single_id},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["task_id"] == single_id


async def test_batch_load_preserves_task_types(authed_client, mock_llm):
    """Each task in batch response has the correct type and type-specific fields."""
    _, tasks = await _create_quiz_and_get_tasks(authed_client)
    task_ids = [t["task_id"] for t in tasks]

    resp = await authed_client.get(
        "/quiz/tasks",
        params=[("task_id", tid) for tid in task_ids],
    )
    data = resp.json()
    types_returned = {t["type"] for t in data}

    # The mock LLM creates one MC, one free text, one cloze
    assert "multiple_choice" in types_returned
    assert "free_text" in types_returned
    assert "cloze" in types_returned

    for task in data:
        if task["type"] == "multiple_choice":
            assert "options" in task
        elif task["type"] == "free_text":
            assert "reference_answer" in task
        elif task["type"] == "cloze":
            assert "template_text" in task
            assert "blanks" in task


# ============================================================================
# Empty / no params
# ============================================================================


async def test_batch_load_no_params_returns_empty(authed_client, mock_llm):
    """GET /quiz/tasks without task_id params returns empty list."""
    resp = await authed_client.get("/quiz/tasks")

    assert resp.status_code == 200
    assert resp.json() == []


# ============================================================================
# Authorization tests
# ============================================================================


async def test_batch_load_unauthenticated_returns_401(client, mock_llm):
    """Unauthenticated requests are rejected."""
    resp = await client.get(
        "/quiz/tasks",
        params={"task_id": "00000000-0000-0000-0000-000000000001"},
    )

    assert resp.status_code == 401 or resp.status_code == 403


async def test_batch_load_other_user_denied(
    authed_client,
    client,
    auth_headers,
    other_user_id,
    mock_llm,
):
    """A user without access to the quiz gets 403."""
    _, tasks = await _create_quiz_and_get_tasks(authed_client)
    task_ids = [t["task_id"] for t in tasks]

    resp = await client.get(
        "/quiz/tasks",
        params=[("task_id", tid) for tid in task_ids],
        headers=auth_headers(other_user_id),
    )

    assert resp.status_code == 403


async def test_batch_load_shared_viewer_allowed(
    authed_client,
    client,
    auth_headers,
    other_user_id,
    mock_llm,
):
    """A viewer who redeemed a share link can batch-load tasks."""
    quiz_id, tasks = await _create_quiz_and_get_tasks(authed_client)
    task_ids = [t["task_id"] for t in tasks]

    # Owner creates share link
    link_resp = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/share-links",
        json={},
    )
    assert link_resp.status_code == 201
    token = link_resp.json()["token"]

    # Other user redeems
    redeem_resp = await client.post(
        f"/quiz/share/{token}/redeem",
        headers=auth_headers(other_user_id),
    )
    assert redeem_resp.status_code == 204

    # Other user can now batch-load
    resp = await client.get(
        "/quiz/tasks",
        params=[("task_id", tid) for tid in task_ids],
        headers=auth_headers(other_user_id),
    )

    assert resp.status_code == 200
    assert len(resp.json()) == len(tasks)


# ============================================================================
# _links in AttemptDetailResponse
# ============================================================================


async def test_attempt_detail_contains_links(authed_client, mock_llm):
    """GET /learning/attempts/{id} includes _links.tasks URL."""
    quiz_id, tasks = await _create_quiz_and_get_tasks(authed_client)

    # Start attempt
    attempt_resp = await authed_client.post(
        f"/learning/quizzes/{quiz_id}/attempts",
    )
    assert attempt_resp.status_code in (200, 201)
    attempt_id = attempt_resp.json()["attempt_id"]

    # Save at least one answer so answers list is non-empty
    first_task = tasks[0]
    answer_payload = build_answer_payload(first_task)
    save_resp = await authed_client.put(
        f"/learning/attempts/{attempt_id}/answers/{first_task['task_id']}",
        json=answer_payload,
    )
    assert save_resp.status_code == 200

    # Get attempt detail
    detail_resp = await authed_client.get(
        f"/learning/attempts/{attempt_id}",
    )
    assert detail_resp.status_code == 200
    data = detail_resp.json()

    # _links should be present because there are answers
    assert "_links" in data
    assert "tasks" in data["_links"]

    tasks_url = data["_links"]["tasks"]
    assert "/quiz/tasks?" in tasks_url
    assert "task_id=" in tasks_url


async def test_attempt_detail_no_links_when_no_answers(authed_client, mock_llm):
    """GET /learning/attempts/{id} omits _links when no answers exist."""
    quiz_id, _ = await _create_quiz_and_get_tasks(authed_client)

    # Start attempt (no answers saved)
    attempt_resp = await authed_client.post(
        f"/learning/quizzes/{quiz_id}/attempts",
    )
    assert attempt_resp.status_code in (200, 201)
    attempt_id = attempt_resp.json()["attempt_id"]

    detail_resp = await authed_client.get(
        f"/learning/attempts/{attempt_id}",
    )
    assert detail_resp.status_code == 200
    data = detail_resp.json()

    # No answers → _links should be null
    assert data.get("_links") is None


async def test_links_url_is_callable(authed_client, mock_llm):
    """The URL from _links.tasks actually returns the correct tasks."""
    quiz_id, tasks = await _create_quiz_and_get_tasks(authed_client)

    # Start attempt and save answers for all tasks
    attempt_resp = await authed_client.post(
        f"/learning/quizzes/{quiz_id}/attempts",
    )
    attempt_id = attempt_resp.json()["attempt_id"]

    for task in tasks:
        payload = build_answer_payload(task)
        await authed_client.put(
            f"/learning/attempts/{attempt_id}/answers/{task['task_id']}",
            json=payload,
        )

    # Get the _links URL
    detail_resp = await authed_client.get(
        f"/learning/attempts/{attempt_id}",
    )
    links_url = detail_resp.json()["_links"]["tasks"]

    # Call the URL directly (strip base to get path + query)
    # The URL looks like http://test/quiz/tasks?task_id=...
    path = links_url.replace("http://test", "")
    batch_resp = await authed_client.get(path)

    assert batch_resp.status_code == 200
    batch_data = batch_resp.json()
    assert len(batch_data) == len(tasks)
