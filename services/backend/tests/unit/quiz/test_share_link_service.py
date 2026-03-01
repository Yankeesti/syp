"""Tests for ShareLinkService business logic."""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.quiz.services.share_link_service import ShareLinkService
from app.modules.quiz.models.quiz_ownership import OwnershipRole


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    mock = AsyncMock()
    # Create async context manager for transaction
    context_manager = AsyncMock()
    context_manager.__aenter__ = AsyncMock(return_value=context_manager)
    context_manager.__aexit__ = AsyncMock(return_value=None)
    mock.begin = MagicMock(return_value=context_manager)
    return mock


@pytest.fixture
def mock_repo():
    """Create mock ShareLinkRepository."""
    return AsyncMock()


@pytest.fixture
def mock_quiz_repo():
    """Create mock QuizRepository."""
    return AsyncMock()


@pytest.fixture
def mock_ownership_repo():
    """Create mock QuizOwnershipRepository."""
    return AsyncMock()


@pytest.fixture
def service(mock_db, mock_repo, mock_quiz_repo, mock_ownership_repo):
    """Create ShareLinkService with mocked dependencies."""
    return ShareLinkService(mock_db, mock_repo, mock_quiz_repo, mock_ownership_repo)


@pytest.fixture
def user_id():
    """Create a sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def quiz_id():
    """Create a sample quiz ID."""
    return uuid.uuid4()


@pytest.fixture
def share_link_id():
    """Create a sample share link ID."""
    return uuid.uuid4()


class TestShareLinkServiceCreate:
    """Tests for ShareLinkService.create_share_link method."""

    @patch("app.modules.quiz.services.share_link_service.secrets.token_urlsafe")
    @patch("app.modules.quiz.services.share_link_service.get_settings")
    async def test_create_share_link_success(
        self,
        mock_get_settings,
        mock_token_urlsafe,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test creating a share link with valid permissions."""
        # Setup
        mock_ownership_repo.user_has_access.return_value = True
        mock_token_urlsafe.return_value = "test_token_123"
        mock_settings = MagicMock()
        mock_settings.frontend_base_url = "https://example.com"
        mock_get_settings.return_value = mock_settings

        # Create mock share link
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.token = "test_token_123"
        mock_link.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_link.expires_at = None
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_link.is_active = True
        mock_repo.create.return_value = mock_link

        # Execute
        result = await service.create_share_link(
            quiz_id=quiz_id,
            user_id=user_id,
        )

        # Verify authorization check
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )

        # Verify repository call
        mock_repo.create.assert_called_once_with(
            quiz_id=quiz_id,
            token="test_token_123",
            created_by=user_id,
            expires_at=None,
            max_uses=None,
        )

        # Verify result
        assert result.share_link_id == share_link_id
        assert result.quiz_id == quiz_id
        assert result.token == "test_token_123"
        assert result.url == "https://example.com/share/test_token_123"
        assert result.current_uses == 0
        assert result.is_active is True

    async def test_create_share_link_forbidden(
        self,
        service,
        mock_ownership_repo,
        user_id,
        quiz_id,
    ):
        """Test creating a share link raises HTTPException(403) when user is not OWNER/EDITOR."""
        # Setup
        mock_ownership_repo.user_has_access.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.create_share_link(
                quiz_id=quiz_id,
                user_id=user_id,
            )

        assert exc_info.value.status_code == 403
        assert "do not have permission" in exc_info.value.detail
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )

    @patch("app.modules.quiz.services.share_link_service.datetime")
    @patch("app.modules.quiz.services.share_link_service.secrets.token_urlsafe")
    @patch("app.modules.quiz.services.share_link_service.get_settings")
    async def test_create_share_link_with_expiration(
        self,
        mock_get_settings,
        mock_token_urlsafe,
        mock_datetime,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test creating a share link with duration."""
        # Setup
        duration = timedelta(days=7)
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expected_expires_at = now + duration

        mock_datetime.now.return_value = now
        mock_ownership_repo.user_has_access.return_value = True
        mock_token_urlsafe.return_value = "test_token_123"
        mock_settings = MagicMock()
        mock_settings.frontend_base_url = "https://example.com"
        mock_get_settings.return_value = mock_settings

        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.token = "test_token_123"
        mock_link.created_at = now
        mock_link.expires_at = expected_expires_at
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_link.is_active = True
        mock_repo.create.return_value = mock_link

        # Execute
        result = await service.create_share_link(
            quiz_id=quiz_id,
            user_id=user_id,
            duration=duration,
        )

        # Verify repository call includes computed expires_at
        mock_repo.create.assert_called_once_with(
            quiz_id=quiz_id,
            token="test_token_123",
            created_by=user_id,
            expires_at=expected_expires_at,
            max_uses=None,
        )

        # Verify result
        assert result.expires_at == expected_expires_at

    @patch("app.modules.quiz.services.share_link_service.secrets.token_urlsafe")
    @patch("app.modules.quiz.services.share_link_service.get_settings")
    async def test_create_share_link_with_max_uses(
        self,
        mock_get_settings,
        mock_token_urlsafe,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test creating a share link with max_uses."""
        # Setup
        max_uses = 10
        mock_ownership_repo.user_has_access.return_value = True
        mock_token_urlsafe.return_value = "test_token_123"
        mock_settings = MagicMock()
        mock_settings.frontend_base_url = "https://example.com"
        mock_get_settings.return_value = mock_settings

        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.token = "test_token_123"
        mock_link.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_link.expires_at = None
        mock_link.max_uses = max_uses
        mock_link.current_uses = 0
        mock_link.is_active = True
        mock_repo.create.return_value = mock_link

        # Execute
        result = await service.create_share_link(
            quiz_id=quiz_id,
            user_id=user_id,
            max_uses=max_uses,
        )

        # Verify repository call includes max_uses
        mock_repo.create.assert_called_once_with(
            quiz_id=quiz_id,
            token="test_token_123",
            created_by=user_id,
            expires_at=None,
            max_uses=max_uses,
        )

        # Verify result
        assert result.max_uses == max_uses


class TestShareLinkServiceList:
    """Tests for ShareLinkService.get_share_links method."""

    @patch("app.modules.quiz.services.share_link_service.get_settings")
    async def test_get_share_links_success(
        self,
        mock_get_settings,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
    ):
        """Test getting a list of share links."""
        # Setup
        mock_ownership_repo.user_has_access.return_value = True
        mock_settings = MagicMock()
        mock_settings.frontend_base_url = "https://example.com"
        mock_get_settings.return_value = mock_settings

        # Create mock share links
        mock_link1 = MagicMock()
        mock_link1.share_link_id = uuid.uuid4()
        mock_link1.quiz_id = quiz_id
        mock_link1.token = "token_1"
        mock_link1.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_link1.expires_at = None
        mock_link1.max_uses = None
        mock_link1.current_uses = 5
        mock_link1.is_active = True

        mock_link2 = MagicMock()
        mock_link2.share_link_id = uuid.uuid4()
        mock_link2.quiz_id = quiz_id
        mock_link2.token = "token_2"
        mock_link2.created_at = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        mock_link2.expires_at = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        mock_link2.max_uses = 10
        mock_link2.current_uses = 3
        mock_link2.is_active = True

        mock_repo.get_by_quiz_id.return_value = [mock_link1, mock_link2]

        # Execute
        result = await service.get_share_links(quiz_id=quiz_id, user_id=user_id)

        # Verify authorization check
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )

        # Verify repository call
        mock_repo.get_by_quiz_id.assert_called_once_with(quiz_id)

        # Verify result
        assert len(result) == 2
        assert result[0].token == "token_1"
        assert result[0].url == "https://example.com/share/token_1"
        assert result[0].current_uses == 5
        assert result[1].token == "token_2"
        assert result[1].url == "https://example.com/share/token_2"
        assert result[1].current_uses == 3

    async def test_get_share_links_forbidden(
        self,
        service,
        mock_ownership_repo,
        user_id,
        quiz_id,
    ):
        """Test getting share links raises HTTPException(403) when user is not OWNER/EDITOR."""
        # Setup
        mock_ownership_repo.user_has_access.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.get_share_links(quiz_id=quiz_id, user_id=user_id)

        assert exc_info.value.status_code == 403
        assert "do not have permission" in exc_info.value.detail
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )

    async def test_get_share_links_empty(
        self,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
    ):
        """Test getting share links returns empty list."""
        # Setup
        mock_ownership_repo.user_has_access.return_value = True
        mock_repo.get_by_quiz_id.return_value = []

        # Execute
        result = await service.get_share_links(quiz_id=quiz_id, user_id=user_id)

        # Verify
        assert isinstance(result, list)
        assert len(result) == 0
        mock_repo.get_by_quiz_id.assert_called_once_with(quiz_id)


class TestShareLinkServiceRevoke:
    """Tests for ShareLinkService.revoke_share_link method."""

    async def test_revoke_share_link_success(
        self,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test revoking a share link successfully."""
        # Setup
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_repo.get_by_id.return_value = mock_link
        mock_ownership_repo.user_has_access.return_value = True

        # Execute
        await service.revoke_share_link(
            share_link_id=share_link_id,
            user_id=user_id,
        )

        # Verify
        mock_repo.get_by_id.assert_called_once_with(share_link_id)
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )
        mock_repo.revoke.assert_called_once_with(share_link_id)

    async def test_revoke_share_link_not_found(
        self,
        service,
        mock_repo,
        user_id,
        share_link_id,
    ):
        """Test revoking a share link raises HTTPException(404) when not found."""
        # Setup
        mock_repo.get_by_id.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.revoke_share_link(
                share_link_id=share_link_id,
                user_id=user_id,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail
        mock_repo.get_by_id.assert_called_once_with(share_link_id)

    async def test_revoke_share_link_forbidden(
        self,
        service,
        mock_ownership_repo,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test revoking a share link raises HTTPException(403) when user lacks permission."""
        # Setup
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_repo.get_by_id.return_value = mock_link
        mock_ownership_repo.user_has_access.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.revoke_share_link(
                share_link_id=share_link_id,
                user_id=user_id,
            )

        assert exc_info.value.status_code == 403
        assert "do not have permission" in exc_info.value.detail
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )


class TestShareLinkServiceValidate:
    """Tests for ShareLinkService.validate_share_link method."""

    async def test_validate_share_link_success(
        self,
        service,
        mock_repo,
        mock_quiz_repo,
        quiz_id,
    ):
        """Test validating a share link returns valid info."""
        # Setup
        token = "test_token_123"
        mock_link = MagicMock()
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = None
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_repo.get_by_token.return_value = mock_link

        mock_quiz = MagicMock()
        mock_quiz.quiz_id = quiz_id
        mock_quiz.title = "Test Quiz"
        mock_quiz.topic = "Test Topic"
        mock_quiz_repo.get_by_id.return_value = mock_quiz

        # Execute
        result = await service.validate_share_link(token)

        # Verify
        mock_repo.get_by_token.assert_called_once_with(token)
        mock_quiz_repo.get_by_id.assert_called_once_with(quiz_id)
        assert result.is_valid is True
        assert result.quiz_id == quiz_id
        assert result.quiz_title == "Test Quiz"
        assert result.quiz_topic == "Test Topic"
        assert result.error_message is None

    async def test_validate_share_link_not_found(
        self,
        service,
        mock_repo,
    ):
        """Test validating a share link returns is_valid=False when not found."""
        # Setup
        token = "invalid_token"
        mock_repo.get_by_token.return_value = None

        # Execute
        result = await service.validate_share_link(token)

        # Verify
        mock_repo.get_by_token.assert_called_once_with(token)
        assert result.is_valid is False
        assert "not found" in result.error_message.lower()

    @patch("app.modules.quiz.services.share_link_service.datetime")
    async def test_validate_share_link_expired(
        self,
        mock_datetime,
        service,
        mock_repo,
        quiz_id,
    ):
        """Test validating a share link returns is_valid=False with 'expired' message."""
        # Setup
        token = "expired_token"
        now = datetime(2024, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
        expired_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        mock_datetime.now.return_value = now

        mock_link = MagicMock()
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = expired_at
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_repo.get_by_token.return_value = mock_link

        # Execute
        result = await service.validate_share_link(token)

        # Verify
        assert result.is_valid is False
        assert "expired" in result.error_message.lower()

    async def test_validate_share_link_max_uses_reached(
        self,
        service,
        mock_repo,
        quiz_id,
    ):
        """Test validating a share link returns is_valid=False with 'maximum uses' message."""
        # Setup
        token = "max_uses_token"
        mock_link = MagicMock()
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = None
        mock_link.max_uses = 5
        mock_link.current_uses = 5
        mock_repo.get_by_token.return_value = mock_link

        # Execute
        result = await service.validate_share_link(token)

        # Verify
        assert result.is_valid is False
        assert "maximum uses" in result.error_message.lower()


class TestShareLinkServiceRedeem:
    """Tests for ShareLinkService.redeem_share_link method."""

    async def test_redeem_share_link_success(
        self,
        service,
        mock_db,
        mock_repo,
        mock_ownership_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test redeeming a share link creates ownership and increments uses."""
        # Setup
        token = "test_token_123"
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = None
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_repo.get_by_token_for_update.return_value = mock_link
        mock_ownership_repo.get_by_quiz_and_user.return_value = None

        # Execute
        await service.redeem_share_link(token, user_id)

        # Verify transaction started
        mock_db.begin.assert_called_once()

        # Verify checks
        mock_repo.get_by_token_for_update.assert_called_once_with(token)
        mock_ownership_repo.get_by_quiz_and_user.assert_called_once_with(
            quiz_id,
            user_id,
        )

        # Verify ownership created
        mock_ownership_repo.create.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
            role=OwnershipRole.VIEWER,
        )

        # Verify usage incremented
        mock_repo.increment_uses.assert_called_once_with(share_link_id)

    async def test_redeem_share_link_not_found(
        self,
        service,
        mock_repo,
        user_id,
    ):
        """Test redeeming a share link raises HTTPException(410) when not found."""
        # Setup
        token = "invalid_token"
        mock_repo.get_by_token_for_update.return_value = None

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.redeem_share_link(token, user_id)

        assert exc_info.value.status_code == 410
        assert "not found" in exc_info.value.detail.lower()

    @patch("app.modules.quiz.services.share_link_service.datetime")
    async def test_redeem_share_link_expired(
        self,
        mock_datetime,
        service,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test redeeming a share link raises HTTPException(410) when expired."""
        # Setup
        token = "expired_token"
        now = datetime(2024, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
        expired_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        mock_datetime.now.return_value = now

        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = expired_at
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_repo.get_by_token_for_update.return_value = mock_link

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.redeem_share_link(token, user_id)

        assert exc_info.value.status_code == 410
        assert "expired" in exc_info.value.detail.lower()

    async def test_redeem_share_link_max_uses_reached(
        self,
        service,
        mock_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test redeeming a share link raises HTTPException(410) when max uses reached."""
        # Setup
        token = "max_uses_token"
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = None
        mock_link.max_uses = 5
        mock_link.current_uses = 5
        mock_repo.get_by_token_for_update.return_value = mock_link

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.redeem_share_link(token, user_id)

        assert exc_info.value.status_code == 410
        assert "maximum uses" in exc_info.value.detail.lower()

    async def test_redeem_share_link_already_has_access(
        self,
        service,
        mock_repo,
        mock_ownership_repo,
        user_id,
        quiz_id,
        share_link_id,
    ):
        """Test redeeming a share link raises HTTPException(400) when user already has access."""
        # Setup
        token = "test_token_123"
        mock_link = MagicMock()
        mock_link.share_link_id = share_link_id
        mock_link.quiz_id = quiz_id
        mock_link.expires_at = None
        mock_link.max_uses = None
        mock_link.current_uses = 0
        mock_repo.get_by_token_for_update.return_value = mock_link

        # User already has ownership
        existing_ownership = MagicMock()
        mock_ownership_repo.get_by_quiz_and_user.return_value = existing_ownership

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await service.redeem_share_link(token, user_id)

        assert exc_info.value.status_code == 400
        assert "already have access" in exc_info.value.detail.lower()
        mock_ownership_repo.get_by_quiz_and_user.assert_called_once_with(
            quiz_id,
            user_id,
        )
