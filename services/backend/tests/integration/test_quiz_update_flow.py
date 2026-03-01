import pytest

pytestmark = pytest.mark.integration


async def _create_quiz_and_tasks(authed_client):
    create = await authed_client.post(
        "/quiz/quizzes",
        data={"user_description": "Testing"},
    )
    assert create.status_code == 202
    quiz_id = create.json()["quiz_id"]

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    tasks = detail.json()["tasks"]
    assert tasks
    return quiz_id, tasks


async def _start_edit_session(authed_client, quiz_id):
    resp = await authed_client.post(f"/quiz/quizzes/{quiz_id}/edit/start")
    assert resp.status_code == 201
    payload = resp.json()
    return payload["edit_session_id"], payload["quiz"]["tasks"]


def _task_by_type(tasks, task_type):
    for task in tasks:
        if task["type"] == task_type:
            return task
    raise AssertionError(f"Task type {task_type} not found")


async def test_update_multiple_choice_task(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    edit_session_id, draft_tasks = await _start_edit_session(
        authed_client,
        quiz_id,
    )
    task = _task_by_type(draft_tasks, "multiple_choice")

    payload = {
        "type": "multiple_choice",
        "prompt": "Welche Aussage trifft zu?",
        "topic_detail": "Updated topic",
        "options": [
            {
                "text": "Option A",
                "is_correct": True,
                "explanation": "Das ist korrekt.",
            },
            {
                "text": "Option B",
                "is_correct": False,
                "explanation": None,
            },
        ],
    }

    resp = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
        headers={"X-Edit-Session-Id": edit_session_id},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["prompt"] == payload["prompt"]
    assert updated["topic_detail"] == payload["topic_detail"]
    option_texts = {option["text"] for option in updated["options"]}
    assert option_texts == {"Option A", "Option B"}

    commit = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/commit",
        json={"edit_session_id": edit_session_id},
    )
    assert commit.status_code == 200

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    persisted = _task_by_type(detail.json()["tasks"], "multiple_choice")
    assert persisted["prompt"] == payload["prompt"]


async def test_update_free_text_task(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    edit_session_id, draft_tasks = await _start_edit_session(
        authed_client,
        quiz_id,
    )
    task = _task_by_type(draft_tasks, "free_text")

    payload = {
        "type": "free_text",
        "prompt": "Beschreibe das Thema in einem Satz.",
        "topic_detail": "Updated topic",
        "reference_answer": "Eine kurze Beispielantwort.",
    }

    resp = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
        headers={"X-Edit-Session-Id": edit_session_id},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["prompt"] == payload["prompt"]
    assert updated["reference_answer"] == payload["reference_answer"]

    commit = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/commit",
        json={"edit_session_id": edit_session_id},
    )
    assert commit.status_code == 200

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    persisted = _task_by_type(detail.json()["tasks"], "free_text")
    assert persisted["reference_answer"] == payload["reference_answer"]


async def test_update_cloze_task(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    edit_session_id, draft_tasks = await _start_edit_session(
        authed_client,
        quiz_id,
    )
    task = _task_by_type(draft_tasks, "cloze")

    payload = {
        "type": "cloze",
        "prompt": "Ergaenze den Satz.",
        "topic_detail": "Updated topic",
        "template_text": "In {{blank_1}} steht {{blank_2}}.",
        "blanks": [
            {"position": 1, "expected_value": "Berlin"},
            {"position": 2, "expected_value": "Deutschland"},
        ],
    }

    resp = await authed_client.put(
        f"/quiz/tasks/{task['task_id']}",
        json=payload,
        headers={"X-Edit-Session-Id": edit_session_id},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["template_text"] == payload["template_text"]
    assert [blank["expected_value"] for blank in updated["blanks"]] == [
        "Berlin",
        "Deutschland",
    ]

    commit = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/commit",
        json={"edit_session_id": edit_session_id},
    )
    assert commit.status_code == 200

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    persisted = _task_by_type(detail.json()["tasks"], "cloze")
    assert persisted["template_text"] == payload["template_text"]


async def test_delete_task_removes_from_quiz(authed_client, mock_llm):
    quiz_id, tasks = await _create_quiz_and_tasks(authed_client)
    edit_session_id, draft_tasks = await _start_edit_session(
        authed_client,
        quiz_id,
    )
    task_id = draft_tasks[0]["task_id"]

    resp = await authed_client.delete(
        f"/quiz/tasks/{task_id}",
        headers={"X-Edit-Session-Id": edit_session_id},
    )
    assert resp.status_code == 204

    commit = await authed_client.post(
        f"/quiz/quizzes/{quiz_id}/edit/commit",
        json={"edit_session_id": edit_session_id},
    )
    assert commit.status_code == 200

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    task_ids = {task["task_id"] for task in detail.json()["tasks"]}
    assert task_id not in task_ids
    assert len(task_ids) == len(tasks) - 1
