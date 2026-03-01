"""Task model to DTO mappings."""

from app.modules.quiz.models.task import Task
from app.modules.quiz.schemas import TaskDetailDto
from app.modules.quiz.strategies import (
    TaskMappingRegistry,
    normalize_task_type,
    task_mapping_registry,
)


def task_to_dto(
    task: Task,
    registry: TaskMappingRegistry | None = None,
) -> TaskDetailDto:
    """Convert Task model to TaskDetailDto."""
    registry = registry or task_mapping_registry()
    task_type = normalize_task_type(task.type)
    return registry.get(task_type).to_dto(task)
