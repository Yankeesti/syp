Integration Tests

Ziel
- End-to-end Tests fuer API-Flows (Quiz -> Attempts -> Evaluation) mit echtem
  FastAPI Routing, DB und Auth, aber deterministisch dank LLM-Mock.

Wichtige Fixtures (tests/integration/conftest.py)
- `app`: erstellt pro Test eine SQLite-Datei-DB, setzt `DATABASE_URL` und
  `JWT_SECRET_KEY`, und registriert alle Modelle.
- `client`: AsyncClient ohne Default-Auth (fuer 401/403 Tests).
- `authed_client`: AsyncClient mit gueltigem JWT fuer `test_user_id`.
- `auth_headers(user_id)`: baut gueltige Authorization-Header fuer einen User.
- `expired_auth_headers(user_id)`: baut einen bereits abgelaufenen Token.
- `mock_llm`: patched `LLMService.generate_quiz` auf ein fixes Quiz.
- `llm_quiz_output`: Default-Quiz fuer den LLM-Mock (kann in Tests ueberschrieben
  werden).

Helpers (tests/integration/helpers.py)
- `build_default_quiz_output(...)`: Standard-Quiz fuer LLM-Mocking.
- `build_answer_payload(task_dict)`: erzeugt eine passende Antwort fuer ein Task-DTO.
- `build_expired_token(user_id)`: erzeugt einen abgelaufenen JWT.

Beispiel: Positiver Flow
```python
import pytest
from tests.integration.helpers import build_answer_payload

pytestmark = pytest.mark.integration


async def test_quiz_flow(authed_client, mock_llm):
    create = await authed_client.post(
        "/quiz/quizzes",
        data={"user_description": "Testing"},
    )
    assert create.status_code == 202
    quiz_id = create.json()["quiz_id"]

    detail = await authed_client.get(f"/quiz/quizzes/{quiz_id}")
    assert detail.status_code == 200
    tasks = detail.json()["tasks"]

    attempt = await authed_client.post(f"/learning/quizzes/{quiz_id}/attempts")
    assert attempt.status_code in {200, 201}
    attempt_id = attempt.json()["attempt_id"]

    for task in tasks:
        payload = build_answer_payload(task)
        await authed_client.put(
            f"/learning/attempts/{attempt_id}/answers/{task['task_id']}",
            json=payload,
        )

    # Optional: Free-Text manuell als korrekt markieren
    for task in tasks:
        if task["type"] == "free_text":
            await authed_client.patch(
                f"/learning/attempts/{attempt_id}/answers/{task['task_id']}/free-text-correctness",
                json={"is_correct": True},
            )

    evaluation = await authed_client.post(
        f"/learning/attempts/{attempt_id}/evaluation",
    )
    assert evaluation.status_code == 200
```

Beispiel: Negative Auth
```python
import pytest

pytestmark = pytest.mark.integration


async def test_invalid_token_rejected(client):
    resp = await client.get(
        "/quiz/quizzes",
        headers={"Authorization": "Bearer invalid.token"},
    )
    assert resp.status_code == 401


async def test_expired_token_rejected(client, expired_auth_headers, test_user_id):
    resp = await client.get(
        "/quiz/quizzes",
        headers=expired_auth_headers(test_user_id),
    )
    assert resp.status_code == 401
```

Beispiel: Zugriff verweigert (403)
```python
import pytest

pytestmark = pytest.mark.integration


async def test_access_denied(client, auth_headers, test_user_id, other_user_id, mock_llm):
    create = await client.post(
        "/quiz/quizzes",
        headers=auth_headers(test_user_id),
        data={"user_description": "Testing"},
    )
    quiz_id = create.json()["quiz_id"]

    resp = await client.get(
        f"/quiz/quizzes/{quiz_id}",
        headers=auth_headers(other_user_id),
    )
    assert resp.status_code == 403
```

Ausfuehren
- Alle Integrationstests: `poetry run pytest tests/integration`
- Nur Integration-Marker: `poetry run pytest -m integration`
