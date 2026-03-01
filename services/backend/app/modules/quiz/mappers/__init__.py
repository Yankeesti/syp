"""Quiz module mappers."""

from app.modules.quiz.mappers.quiz_mapper import (
    quiz_to_detail_response,
    quiz_to_list_item,
)
from app.modules.quiz.mappers.task_mapper import task_to_dto

__all__ = ["quiz_to_detail_response", "quiz_to_list_item", "task_to_dto"]
