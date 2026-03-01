"""Account-related services for the auth module."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.repositories.user_repository import UserRepository


class AccountService:
    """Service for user account operations."""

    def __init__(self, db: AsyncSession, user_repo: UserRepository):
        self.db = db
        self.user_repo = user_repo

    async def delete_user_account(self, user_id: uuid.UUID) -> bool:
        """Delete a user account and commit the transaction.

        Returns True if a user was deleted, False otherwise.
        """
        deleted = await self.user_repo.delete(user_id)
        if deleted:
            await self.db.commit()
        return deleted
