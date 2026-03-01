"""Integration tests for the error report endpoint."""

import pytest
from app.modules.auth.dependencies import get_magic_link_service

pytestmark = pytest.mark.integration


async def test_report_error_sends_email(authed_client):
    """Posting a report triggers MailService.send (dependency overridden)."""
    from app.main import app as fastapi_app
    from app.shared.dependencies import get_mailer

    sent = {}

    class FakeMailer:
        sender = "KITutorTH@gmail.com"

        async def send(self, to, subject, html, text=None):
            sent["to"] = to
            sent["subject"] = subject
            sent["html"] = html
            sent["text"] = text

    # Override mailer dependency
    fastapi_app.dependency_overrides[get_mailer] = lambda: FakeMailer()

    resp = await authed_client.post(
        "/auth/report",
        json={"message": "Testfehler aufgetreten", "contact_email": "u@e.de"},
    )
    assert resp.status_code == 202
    assert sent["to"] == "KITutorTH@gmail.com"
    assert "Testfehler" in sent["html"]


async def test_report_requires_message(authed_client):
    resp = await authed_client.post("/auth/report", json={})
    assert resp.status_code == 422
