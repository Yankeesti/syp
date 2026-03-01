"""Exception handlers for learning module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.learning.exceptions import (
    LearningModuleException,
    AttemptNotFoundException,
    AttemptLockedException,
    QuizNotFoundException,
    QuizNotCompletedException,
    AccessDeniedException,
    TaskNotFoundException,
    AnswerTypeMismatchException,
    AnswerNotFoundException,
    InvalidAnswerTypeException,
)


async def attempt_not_found_handler(
    request: Request,
    exc: AttemptNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def attempt_locked_handler(
    request: Request,
    exc: AttemptLockedException,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


async def quiz_not_found_handler(
    request: Request,
    exc: QuizNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def quiz_not_completed_handler(
    request: Request,
    exc: QuizNotCompletedException,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


async def access_denied_handler(
    request: Request,
    exc: AccessDeniedException,
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )


async def task_not_found_handler(
    request: Request,
    exc: TaskNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def answer_type_mismatch_handler(
    request: Request,
    exc: AnswerTypeMismatchException,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def answer_not_found_handler(
    request: Request,
    exc: AnswerNotFoundException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def invalid_answer_type_handler(
    request: Request,
    exc: InvalidAnswerTypeException,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all learning module exception handlers with the FastAPI app."""
    app.add_exception_handler(AttemptNotFoundException, attempt_not_found_handler)
    app.add_exception_handler(AttemptLockedException, attempt_locked_handler)
    app.add_exception_handler(QuizNotFoundException, quiz_not_found_handler)
    app.add_exception_handler(QuizNotCompletedException, quiz_not_completed_handler)
    app.add_exception_handler(AccessDeniedException, access_denied_handler)
    app.add_exception_handler(TaskNotFoundException, task_not_found_handler)
    app.add_exception_handler(AnswerTypeMismatchException, answer_type_mismatch_handler)
    app.add_exception_handler(AnswerNotFoundException, answer_not_found_handler)
    app.add_exception_handler(InvalidAnswerTypeException, invalid_answer_type_handler)
