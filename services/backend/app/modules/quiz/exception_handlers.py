"""Exception handlers for the quiz module.

Maps domain exceptions to HTTP responses.
Register these handlers with the FastAPI app in main.py.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.quiz.exceptions import (
    QuizNotFoundException,
    TaskNotFoundException,
    AccessDeniedException,
    InvalidTaskTypeException,
    TaskTypeMismatchException,
    EditSessionRequiredException,
    EditSessionNotFoundException,
    EditSessionInactiveException,
    EditSessionTaskMismatchException,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register quiz module exception handlers with the FastAPI app."""

    @app.exception_handler(QuizNotFoundException)
    async def quiz_not_found_handler(request: Request, exc: QuizNotFoundException):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(TaskNotFoundException)
    async def task_not_found_handler(request: Request, exc: TaskNotFoundException):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(AccessDeniedException)
    async def access_denied_handler(request: Request, exc: AccessDeniedException):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(InvalidTaskTypeException)
    async def invalid_task_type_handler(
        request: Request,
        exc: InvalidTaskTypeException,
    ):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(TaskTypeMismatchException)
    async def task_type_mismatch_handler(
        request: Request,
        exc: TaskTypeMismatchException,
    ):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(EditSessionRequiredException)
    async def edit_session_required_handler(
        request: Request,
        exc: EditSessionRequiredException,
    ):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(EditSessionNotFoundException)
    async def edit_session_not_found_handler(
        request: Request,
        exc: EditSessionNotFoundException,
    ):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(EditSessionInactiveException)
    async def edit_session_inactive_handler(
        request: Request,
        exc: EditSessionInactiveException,
    ):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(EditSessionTaskMismatchException)
    async def edit_session_task_mismatch_handler(
        request: Request,
        exc: EditSessionTaskMismatchException,
    ):
        return JSONResponse(status_code=409, content={"detail": exc.message})
