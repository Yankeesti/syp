"""Authentication service for business logic.

This module orchestrates authentication operations including:
- Magic Link generation and verification
- User creation and retrieval
- JWT token generation
"""

import hashlib
import asyncio
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_jwt_token
from app.modules.auth.services.dtos import MagicLinkResult, TokenResult
from app.modules.auth.exceptions import (
    MagicLinkTokenExpiredError,
    MagicLinkTokenInvalidError,
    UserNotRegisteredError,
)
from app.modules.auth.repositories.magic_link_token_repository import (
    MagicLinkTokenRepository,
)
from app.modules.auth.repositories.user_repository import UserRepository
from app.shared.schemas import TokenPayload


from app.shared.dependencies import get_mailer

logger = logging.getLogger(__name__)


class MagicLinkService:
    """Service for Magic Link authentication operations."""

    def __init__(
        self,
        db: AsyncSession,
        user_repo: UserRepository,
        token_repo: MagicLinkTokenRepository,
    ):
        self.db = db
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.settings = get_settings()

    @staticmethod
    def _hash(data: str) -> str:
        """
        Generate SHA-256 hash of input data.

        Args:
            data: String to hash

        Returns:
            Hexadecimal SHA-256 hash (64 characters)
        """
        return hashlib.sha256(data.encode()).hexdigest()

    async def request_magic_link(self, email: str) -> MagicLinkResult:
        """
        Generate and persist a magic link for a registered user.

        Args:
            email: User's email address
        Returns:
            MagicLinkResult with expiration time

        Raises:
            AuthError: Never raised for non-existing users to avoid enumeration
        """
        email_hash = self._hash(email)
        user = await self.user_repo.get_by_email_hash(email_hash)
        if user is None:
            # Return generic response to avoid user enumeration.
            expires_in_seconds = self.settings.magic_link_expiration_minutes * 60
            return MagicLinkResult(expires_in=expires_in_seconds)

        return await self._issue_magic_link(email, email_hash)

    async def register_user_and_request_magic_link(
        self,
        email: str,
    ) -> MagicLinkResult:
        """
        Register a new user and send a magic link.

        Args:
            email: User's email address
        Returns:
            MagicLinkResult with expiration time

        Raises:
            AuthError: Never raised for existing users to avoid enumeration
        """
        email_hash = self._hash(email)
        existing_user = await self.user_repo.get_by_email_hash(email_hash)
        if existing_user is not None:
            # Return response without sending an email.
            expires_in_seconds = self.settings.magic_link_expiration_minutes * 60
            return MagicLinkResult(
                expires_in=expires_in_seconds,
                already_registered=True,
            )

        await self.user_repo.create(email_hash=email_hash)
        return await self._issue_magic_link(
            email,
            email_hash,
            already_registered=False,
        )

    async def _issue_magic_link(
        self,
        email: str,
        email_hash: str,
        already_registered: bool | None = None,
    ) -> MagicLinkResult:
        token = secrets.token_urlsafe(32)

        token_hash = self._hash(token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.magic_link_expiration_minutes,
        )

        # Delete existing token for this email (if any)
        # TODO: Rate-limiting needed - without it, an attacker knowing the email
        # could spam this endpoint to continuously invalidate tokens
        await self.token_repo.delete_by_email_hash(email_hash)

        await self.token_repo.create(
            token_hash=token_hash,
            email_hash=email_hash,
            expires_at=expires_at,
        )

        await self.db.commit()

        frontend_base_url = self.settings.frontend_base_url.rstrip("/")
        magic_link_url = f"{frontend_base_url}/auth/verify?token={token}"

        # Log magic link for debugging
        logger.info(f"Magic Link for {email}: {magic_link_url}")

        # Magic Link per E-Mail versenden (im Hintergrund starten, damit
        # die HTTP-Anfrage nicht auf den E-Mail-Versand warten muss)
        # Fehler beim Versand werden geloggt innerhalb von `send_magic_link`.
        asyncio.create_task(self.send_magic_link(email, magic_link_url))

        expires_in_seconds = self.settings.magic_link_expiration_minutes * 60

        return MagicLinkResult(
            expires_in=expires_in_seconds,
            already_registered=already_registered,
        )

    async def send_magic_link(self, email: str, magic_link: str):
        """
        Versendet den Magic Link per E-Mail an den Benutzer.

        Nutzt den konfigurierten SMTP-Mailservice (siehe app.core.email / Settings).

        Args:
            email: E-Mail-Adresse des Empfängers
            magic_link: Der vollständige Magic-Link-URL

        Raises:
            Exception: Wenn der E-Mail-Versand fehlschlägt
        """
        try:
            mailer = await get_mailer()
            subject, html, text = mailer.build_magic_link_email(email, magic_link)

            await mailer.send(to=email, subject=subject, html=html, text=text)
            logger.info(f"Magic Link email sent successfully to {email}")
        except Exception as e:
            logger.error(
                f"Failed to send magic link email to {email}: {str(e)}",
                exc_info=True,
            )
            # Re-raise exception to ensure error is logged
            raise

    async def verify_magic_link(self, token: str) -> TokenResult:
        """
        Verify magic link token and authenticate user.

        Process:
        1. Hash token and lookup in database
        2. Validate token exists and not expired
        3. Delete token (single-use)
        4. Get user
        5. Generate JWT token

        Args:
            token: The magic link token from URL query parameter

        Returns:
            TokenResult with JWT access token

        Raises:
            MagicLinkTokenInvalidError: Token not found or already used
            MagicLinkTokenExpiredError: Token expired
            UserNotRegisteredError: User not registered

        Notes:
            - Token is deleted after verification (single-use)
            - JWT token is valid for JWT_EXPIRATION_HOURS (default: 5 hours)
        """
        token_hash = self._hash(token)

        magic_link_token = await self.token_repo.get_by_token_hash(token_hash)

        if magic_link_token is None:
            raise MagicLinkTokenInvalidError()

        # Check if token is expired
        if datetime.now(timezone.utc) > magic_link_token.expires_at:
            await self.token_repo.delete(magic_link_token.id)
            await self.db.commit()

            raise MagicLinkTokenExpiredError()

        email_hash = magic_link_token.email_hash

        # Delete token immediately (single-use, prevents reuse)
        await self.token_repo.delete(magic_link_token.id)

        user = await self.user_repo.get_by_email_hash(email_hash)

        if user is None:
            await self.db.commit()
            raise UserNotRegisteredError()

        await self.db.commit()

        # Generate JWT token
        access_token = create_jwt_token(TokenPayload(user_id=user.user_id))

        return TokenResult(access_token=access_token, token_type="bearer")
