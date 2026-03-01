"""Exception handlers for auth module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.auth.exceptions import (
    MagicLinkTokenExpiredError,
    MagicLinkTokenInvalidError,
    UserNotRegisteredError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register auth module exception handlers with the FastAPI app."""

    @app.exception_handler(MagicLinkTokenInvalidError)
    async def magic_link_token_invalid_handler(
        request: Request,
        exc: MagicLinkTokenInvalidError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Invalid or expired token"},
        )

    @app.exception_handler(MagicLinkTokenExpiredError)
    async def magic_link_token_expired_handler(
        request: Request,
        exc: MagicLinkTokenExpiredError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired"},
        )

    @app.exception_handler(UserNotRegisteredError)
    async def user_not_registered_handler(
        request: Request,
        exc: UserNotRegisteredError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "User not registered"},
        )
