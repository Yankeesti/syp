"""Integration tests for account deletion endpoint."""

import pytest

pytestmark = pytest.mark.integration


async def test_delete_account_success(authed_client, test_user_id):
    """Authenticated user with existing DB record can delete their account."""
    from app.core.database import sessionmanager
    from app.modules.auth.models import User

    # Create a user record that matches the JWT subject
    async with sessionmanager.session() as s:
        user = User(user_id=test_user_id, email_hash="delete_account_hash")
        s.add(user)
        await s.flush()
        await s.commit()

    # Call delete endpoint
    resp = await authed_client.delete("/auth/account")
    assert resp.status_code == 204

    # Verify the user was removed from DB
    async with sessionmanager.session() as s:
        found = await s.get(User, test_user_id)
        assert found is None


async def test_delete_account_not_found(authed_client, test_user_id):
    """If no matching user record exists deletion returns 404."""
    resp = await authed_client.delete("/auth/account")
    assert resp.status_code == 404
