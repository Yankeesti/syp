"""Quiz module dependencies for FastAPI dependency injection."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.shared.dependencies import DBSessionDep
from app.modules.quiz.events import get_quiz_event_publisher
from app.modules.quiz.services.quiz_service import QuizService
from app.modules.quiz.strategies import (
    TaskCloneRegistry,
    TaskMappingRegistry,
    TaskUpdateRegistry,
    task_clone_registry,
    task_mapping_registry,
    task_update_registry,
)
from app.modules.quiz.services.task_service import TaskService
from app.modules.quiz.services.share_link_service import ShareLinkService
from app.modules.quiz.repositories.quiz_repository import QuizRepository
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)
from app.modules.quiz.repositories.task_repository import TaskRepository
from app.modules.quiz.repositories.quiz_version_repository import QuizVersionRepository
from app.modules.quiz.repositories.quiz_edit_session_repository import (
    QuizEditSessionRepository,
)
from app.modules.quiz.repositories.share_link_repository import ShareLinkRepository
from app.modules.quiz.services.edit_session_service import QuizEditSessionService
from app.shared.ports.quiz_events import QuizEventPublisher
from app.shared.ports.quiz_generation import QuizGenerationPortDep


# Registry Dependencies
@lru_cache
def get_task_mapping_registry() -> TaskMappingRegistry:
    """Factory for task mapping strategy registry."""
    return task_mapping_registry()


@lru_cache
def get_task_update_registry() -> TaskUpdateRegistry:
    """Factory for task update strategy registry."""
    return task_update_registry()


@lru_cache
def get_task_clone_registry() -> TaskCloneRegistry:
    """Factory for task clone strategy registry."""
    return task_clone_registry()


# Repository Dependencies
def get_quiz_repository(db: DBSessionDep) -> QuizRepository:
    """Dependency that provides a QuizRepository instance."""
    return QuizRepository(db)


def get_quiz_ownership_repository(db: DBSessionDep) -> QuizOwnershipRepository:
    """Dependency that provides a QuizOwnershipRepository instance."""
    return QuizOwnershipRepository(db)


def get_task_repository(db: DBSessionDep) -> TaskRepository:
    """Dependency that provides a TaskRepository instance."""
    return TaskRepository(db)


def get_quiz_version_repository(db: DBSessionDep) -> QuizVersionRepository:
    """Dependency that provides a QuizVersionRepository instance."""
    return QuizVersionRepository(db)


def get_quiz_edit_session_repository(db: DBSessionDep) -> QuizEditSessionRepository:
    """Dependency that provides a QuizEditSessionRepository instance."""
    return QuizEditSessionRepository(db)


def get_share_link_repository(db: DBSessionDep) -> ShareLinkRepository:
    """Dependency that provides a ShareLinkRepository instance."""
    return ShareLinkRepository(db)


# Service Dependencies
def get_quiz_service(
    quiz_repo: Annotated[QuizRepository, Depends(get_quiz_repository)],
    ownership_repo: Annotated[
        QuizOwnershipRepository,
        Depends(get_quiz_ownership_repository),
    ],
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    version_repo: Annotated[
        QuizVersionRepository,
        Depends(get_quiz_version_repository),
    ],
    generation_port: QuizGenerationPortDep,
    event_publisher: QuizEventPublisher = Depends(get_quiz_event_publisher),
    mapping_registry: TaskMappingRegistry = Depends(get_task_mapping_registry),
    db: DBSessionDep = None,
) -> QuizService:
    """Dependency that provides a QuizService instance."""
    return QuizService(
        db,
        quiz_repo,
        ownership_repo,
        task_repo,
        version_repo,
        mapping_registry,
        event_publisher,
        generation_port,
    )


def get_task_service(
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    ownership_repo: Annotated[
        QuizOwnershipRepository,
        Depends(get_quiz_ownership_repository),
    ],
    session_repo: Annotated[
        QuizEditSessionRepository,
        Depends(get_quiz_edit_session_repository),
    ],
    quiz_repo: Annotated[QuizRepository, Depends(get_quiz_repository)],
    version_repo: Annotated[
        QuizVersionRepository,
        Depends(get_quiz_version_repository),
    ],
    mapping_registry: TaskMappingRegistry = Depends(get_task_mapping_registry),
    update_registry: TaskUpdateRegistry = Depends(get_task_update_registry),
    clone_registry: TaskCloneRegistry = Depends(get_task_clone_registry),
    db: DBSessionDep = None,
) -> TaskService:
    """Dependency that provides a TaskService instance."""
    edit_session_service = QuizEditSessionService(
        db,
        quiz_repo,
        ownership_repo,
        task_repo,
        version_repo,
        session_repo,
        mapping_registry,
        clone_registry,
    )
    return TaskService(
        db,
        task_repo,
        ownership_repo,
        edit_session_service,
        mapping_registry,
        update_registry,
    )


def get_quiz_edit_session_service(
    quiz_repo: Annotated[QuizRepository, Depends(get_quiz_repository)],
    ownership_repo: Annotated[
        QuizOwnershipRepository,
        Depends(get_quiz_ownership_repository),
    ],
    task_repo: Annotated[TaskRepository, Depends(get_task_repository)],
    version_repo: Annotated[
        QuizVersionRepository,
        Depends(get_quiz_version_repository),
    ],
    session_repo: Annotated[
        QuizEditSessionRepository,
        Depends(get_quiz_edit_session_repository),
    ],
    mapping_registry: TaskMappingRegistry = Depends(get_task_mapping_registry),
    clone_registry: TaskCloneRegistry = Depends(get_task_clone_registry),
    db: DBSessionDep = None,
) -> QuizEditSessionService:
    """Dependency that provides a QuizEditSessionService instance."""
    return QuizEditSessionService(
        db,
        quiz_repo,
        ownership_repo,
        task_repo,
        version_repo,
        session_repo,
        mapping_registry,
        clone_registry,
    )


def get_share_link_service(
    share_link_repo: Annotated[ShareLinkRepository, Depends(get_share_link_repository)],
    quiz_repo: Annotated[QuizRepository, Depends(get_quiz_repository)],
    ownership_repo: Annotated[
        QuizOwnershipRepository,
        Depends(get_quiz_ownership_repository),
    ],
    db: DBSessionDep = None,
) -> ShareLinkService:
    """Dependency that provides a ShareLinkService instance."""
    return ShareLinkService(db, share_link_repo, quiz_repo, ownership_repo)


# Type aliases for cleaner endpoint signatures
QuizServiceDep = Annotated[QuizService, Depends(get_quiz_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
QuizEditSessionServiceDep = Annotated[
    QuizEditSessionService,
    Depends(get_quiz_edit_session_service),
]
ShareLinkServiceDep = Annotated[ShareLinkService, Depends(get_share_link_service)]
QuizRepositoryDep = Annotated[QuizRepository, Depends(get_quiz_repository)]
QuizOwnershipRepositoryDep = Annotated[
    QuizOwnershipRepository,
    Depends(get_quiz_ownership_repository),
]
TaskRepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]
QuizVersionRepositoryDep = Annotated[
    QuizVersionRepository,
    Depends(get_quiz_version_repository),
]
QuizEditSessionRepositoryDep = Annotated[
    QuizEditSessionRepository,
    Depends(get_quiz_edit_session_repository),
]
ShareLinkRepositoryDep = Annotated[
    ShareLinkRepository,
    Depends(get_share_link_repository),
]
TaskMappingRegistryDep = Annotated[
    TaskMappingRegistry,
    Depends(get_task_mapping_registry),
]
TaskUpdateRegistryDep = Annotated[
    TaskUpdateRegistry,
    Depends(get_task_update_registry),
]
TaskCloneRegistryDep = Annotated[
    TaskCloneRegistry,
    Depends(get_task_clone_registry),
]
