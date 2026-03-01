"""Answer model to DTO mappings."""

from app.modules.learning.models.answer import Answer
from app.modules.learning.schemas.answer import ExistingAnswerDTO
from app.modules.learning.strategies import AnswerMappingRegistry, normalize_answer_type


def answer_to_dto(
    answer: Answer,
    registry: AnswerMappingRegistry,
) -> ExistingAnswerDTO:
    """Convert Answer model to ExistingAnswerDTO."""
    return registry.get(normalize_answer_type(answer.type)).to_dto(answer)
