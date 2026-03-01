"""Authentication API endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.shared.dependencies import CurrentUserId, get_mailer
from app.modules.auth.dependencies import AccountServiceDep, MagicLinkServiceDep
from app.modules.auth.schemas import (
    MagicLinkRequest,
    MagicLinkResponse,
    TokenResponse,
    ReportRequest,
    ReportResponse,
)
from app.core.email import MailService

router = APIRouter(prefix="/auth", tags=["auth"])
MAGIC_LINK_GENERIC_MESSAGE = "If the email is registered, a magic link has been sent"
REGISTER_SUCCESS_MESSAGE = (
    "Registrierung erfolgreich. Wir haben dir einen Login-Link gesendet."
)
REGISTER_ALREADY_REGISTERED_MESSAGE = (
    "Diese E-Mail ist bereits registriert. Bitte melde dich im Login an. "
    "Es wurde kein Link versendet."
)


@router.get("/health")
async def health_check():
    """Health check endpoint for auth module."""
    return {"status": "ok", "module": "auth"}


@router.post(
    "/magic-link",
    response_model=MagicLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Magic Link",
    description="Generate a magic link for passwordless authentication. "
    "If the email is registered, a login link will be sent.",
)
async def request_magic_link(
    request: MagicLinkRequest,
    service: MagicLinkServiceDep,
) -> MagicLinkResponse:
    """
    Request a magic link for passwordless authentication.

    Args:
        request: MagicLinkRequest containing user's email
        db: Database session (injected)

    Returns:
        MagicLinkResponse with generic success message and expiration time

    Raises:
        HTTPException 400: Invalid email format (handled by Pydantic)
    """
    result = await service.request_magic_link(request.email)
    return MagicLinkResponse(
        message=MAGIC_LINK_GENERIC_MESSAGE,
        expires_in=result.expires_in,
    )


@router.post(
    "/register",
    response_model=MagicLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Register and request Magic Link",
    description="Register a new user and send a magic link. "
    "If the email is already registered, a login hint is returned without sending an email.",
)
async def register_user(
    request: MagicLinkRequest,
    service: MagicLinkServiceDep,
) -> MagicLinkResponse:
    """
    Register a new user and send a magic link.

    Args:
        request: MagicLinkRequest containing user's email

    Returns:
        MagicLinkResponse with a contextual success message and expiration time

    Raises:
        HTTPException 400: Invalid email format (handled by Pydantic)
    """
    result = await service.register_user_and_request_magic_link(request.email)
    message = (
        REGISTER_ALREADY_REGISTERED_MESSAGE
        if result.already_registered is True
        else REGISTER_SUCCESS_MESSAGE
    )
    return MagicLinkResponse(
        message=message,
        expires_in=result.expires_in,
    )


@router.get(
    "/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Magic Link",
    description="Verify magic link token and receive JWT access token.",
)
async def verify_magic_link(
    service: MagicLinkServiceDep,
    token: str = Query(..., description="Magic link token from email", min_length=1),
) -> TokenResponse:
    """
    Verify magic link token and authenticate user.

    Process:
    1. Validates token exists and not expired
    2. Deletes token (single-use)
    3. Gets user account
    4. Returns JWT token for authenticated requests

    Args:
        token: Magic link token from URL query parameter
        db: Database session (injected)

    Returns:
        TokenResponse with JWT access token

    Raises:
        HTTPException 400: Token parameter missing
        HTTPException 401: Token expired
        HTTPException 404: Token invalid or already used
        HTTPException 404: User not registered
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token parameter is required",
        )

    result = await service.verify_magic_link(token)
    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
    )


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
    description="Delete the authenticated user's account and related data.",
)
async def delete_account(
    user_id: CurrentUserId,
    service: AccountServiceDep,
):
    """
    Delete the current user's account.

    Uses `AccountService.delete_user_account` to remove the user record.
    Returns 204 on success, 404 if the user was not found.
    """
    deleted = await service.delete_user_account(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return None


@router.post(
    "/report",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportResponse,
    summary="Fehler melden",
    description="Send a short error report to the support mailbox.",
)
async def report_error(
    request: ReportRequest,
    user_id: CurrentUserId,
    mailer: Annotated[MailService, Depends(get_mailer)],
):
    """Report an application error. Sends an email to the configured support address.

    The authenticated user's id is included for context.
    """
    subject = f"Fehlerbericht von Nutzer {user_id}"
    html = f"<p>{request.message}</p>"
    if request.contact_email:
        html += f"<p>Kontakt: {request.contact_email}</p>"

    # Send to configured sender/support mailbox
    await mailer.send(mailer.sender, subject, html, text=request.message)
    return ReportResponse(message="Report received")
