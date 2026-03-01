"""Main FastAPI application with router registration."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.auth.exception_handlers import (
    register_exception_handlers as register_auth_exception_handlers,
)
from app.modules.quiz.router import router as quiz_router
from app.modules.learning.router import router as learning_router
from app.modules.llm.router import router as llm_router
from app.modules.quiz.events import get_quiz_event_publisher
from app.modules.quiz.exception_handlers import (
    register_exception_handlers as register_quiz_exception_handlers,
)
from app.modules.quiz.public.ports import register_quiz_ports
from app.modules.llm.public.ports import register_llm_ports
from app.modules.learning.exception_handlers import (
    register_exception_handlers as register_learning_exception_handlers,
)
from app.modules.learning.public.subscribers import register_quiz_subscribers

settings = get_settings()

root_logger = logging.getLogger()
if not root_logger.handlers:
    uvicorn_level = logging.getLogger("uvicorn.error").getEffectiveLevel()
    if uvicorn_level == logging.NOTSET:
        uvicorn_level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=uvicorn_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered learning platform API with modular monolith architecture (3-Module Structure)",
    debug=settings.debug,
)

# Wire shared ports and register cross-module subscribers.
register_quiz_ports(app)
register_llm_ports(app)
register_quiz_subscribers(get_quiz_event_publisher())

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module exception handlers
register_auth_exception_handlers(app)
register_quiz_exception_handlers(app)
register_learning_exception_handlers(app)

# Register module routers
app.include_router(auth_router)
app.include_router(quiz_router)
app.include_router(learning_router)
app.include_router(llm_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
