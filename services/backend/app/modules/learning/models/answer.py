"""Answer models with polymorphic inheritance.

Based on Wiki Specification:
- Answer is an abstract base with common fields
- Three concrete answer types: MultipleChoice, FreeText, Cloze
- Uses SQLAlchemy Joined Table Inheritance
- Answers reference tasks from quiz module (no FK - cross-module reference)

Architecture:
- Base table 'answer' with common fields and 'type' discriminator
- Type-specific tables with 1:1 FK to base answer table
- Nested entities (selections, items) reference type-specific tables
"""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
    Numeric,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AnswerType(str, enum.Enum):
    """Answer type discriminator for polymorphic inheritance."""

    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"
    CLOZE = "cloze"


class Answer(Base):
    """
    Base answer model (abstract) with common fields for all answer types.

    Uses joined table inheritance - concrete types extend this in separate tables.

    Attributes:
        answer_id: UUID primary key
        attempt_id: UUID foreign key to attempt
        task_id: UUID reference to task (no FK - cross-module reference)
        type: Answer type discriminator (multiple_choice/free_text/cloze)
        percentage_correct: Score as percentage (0-100, nullable until evaluated)

    Relationships:
        attempt: Many-to-one relationship to Attempt
    """

    __tablename__ = "answer"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attempt.attempt_id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to attempt",
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        comment="UUID reference to task",
    )

    type: Mapped[AnswerType] = mapped_column(
        SQLEnum(AnswerType, native_enum=False, length=20),
        nullable=False,
        comment="Answer type discriminator",
    )

    percentage_correct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Score as percentage (0-100)",
    )

    # Polymorphic setup for joined table inheritance
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": None,  # Abstract base, no direct instances
    }

    # Relationship to attempt
    attempt: Mapped["Attempt"] = relationship(
        "Attempt",
        back_populates="answers",
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("attempt_id", "task_id", name="uq_answer_attempt_task"),
        Index("ix_answer_attempt_id", "attempt_id"),
        Index("ix_answer_task_id", "task_id"),
    )


class MultipleChoiceAnswer(Answer):
    """
    Multiple choice answer with selections.

    Extends Answer with a separate table linked via answer_id.
    No additional fields, but has relationship to selections.

    Attributes:
        answer_id: UUID primary key and foreign key to answer.answer_id

    Relationships:
        selections: One-to-many relationship to AnswerMultipleChoiceSelection
    """

    __tablename__ = "answer_multiple_choice"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answer.answer_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base answer",
    )

    __mapper_args__ = {
        "polymorphic_identity": AnswerType.MULTIPLE_CHOICE,
    }

    # Relationship to selections
    selections: Mapped[list["AnswerMultipleChoiceSelection"]] = relationship(
        "AnswerMultipleChoiceSelection",
        back_populates="answer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MultipleChoiceAnswer(answer_id={self.answer_id}, "
            f"task_id={self.task_id}, "
            f"selections_count={len(self.selections) if self.selections else 0})>"
        )


class AnswerMultipleChoiceSelection(Base):
    """
    Selected option for multiple choice answer.

    Represents a single option selected by the user.
    Uses composite primary key (answer_id, option_id).

    Attributes:
        answer_id: UUID foreign key to answer_multiple_choice
        option_id: UUID reference to task option (no FK - cross-module reference)

    Relationships:
        answer: Many-to-one relationship to MultipleChoiceAnswer
    """

    __tablename__ = "answer_multiple_choice_selection"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answer_multiple_choice.answer_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to multiple choice answer",
    )

    option_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        comment="UUID reference to task option",
    )

    # Relationship back to answer
    answer: Mapped["MultipleChoiceAnswer"] = relationship(
        "MultipleChoiceAnswer",
        back_populates="selections",
    )


class FreeTextAnswer(Answer):
    """
    Free text answer with user's text response.

    Extends Answer with text_response field for LLM-based evaluation.

    Attributes:
        answer_id: UUID primary key and foreign key to answer.answer_id
        text_response: User's written answer text
    """

    __tablename__ = "answer_free_text"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answer.answer_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base answer",
    )

    text_response: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's written answer text",
    )

    __mapper_args__ = {
        "polymorphic_identity": AnswerType.FREE_TEXT,
    }


class ClozeAnswer(Answer):
    """
    Cloze (fill-in-the-blank) answer.

    Extends Answer with items for each blank filled by the user.

    Attributes:
        answer_id: UUID primary key and foreign key to answer.answer_id

    Relationships:
        items: One-to-many relationship to AnswerClozeItem
    """

    __tablename__ = "answer_cloze"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answer.answer_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base answer",
    )

    __mapper_args__ = {
        "polymorphic_identity": AnswerType.CLOZE,
    }

    # Relationship to cloze items
    items: Mapped[list["AnswerClozeItem"]] = relationship(
        "AnswerClozeItem",
        back_populates="answer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ClozeAnswer(answer_id={self.answer_id}, "
            f"task_id={self.task_id}, "
            f"items_count={len(self.items) if self.items else 0})>"
        )


class AnswerClozeItem(Base):
    """
    Filled blank for cloze answer.

    Represents a single blank filled by the user with correctness evaluation.
    Uses composite primary key (answer_id, blank_id).

    Attributes:
        answer_id: UUID foreign key to answer_cloze
        blank_id: UUID reference to task blank (no FK - cross-module reference)
        provided_value: User's provided text for this blank
        is_correct: Whether the provided value is correct (nullable until evaluated)

    Relationships:
        answer: Many-to-one relationship to ClozeAnswer
    """

    __tablename__ = "answer_cloze_item"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answer_cloze.answer_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to cloze answer",
    )

    blank_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        comment="UUID reference to task blank",
    )

    provided_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User's provided text for this blank",
    )

    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether the provided value is correct",
    )

    # Relationship back to answer
    answer: Mapped["ClozeAnswer"] = relationship(
        "ClozeAnswer",
        back_populates="items",
    )
