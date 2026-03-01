"""Task models with polymorphic inheritance.

Based on Wiki Specification:
- Task is an abstract base with common fields
- Three concrete task types: MultipleChoice, FreeText, Cloze
- Uses SQLAlchemy Joined Table Inheritance
- Tasks cannot exist without a quiz (child entity)

Architecture:
- Base table 'task' with common fields and 'type' discriminator
- Type-specific tables with 1:1 FK to base task table
- Nested entities (options, blanks) reference type-specific tables
"""

import uuid

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums import TaskType


class Task(Base):
    """
    Base task model (abstract) with common fields for all task types.

    Uses joined table inheritance - concrete types extend this in separate tables.

    Attributes:
        task_id: UUID primary key
        quiz_id: UUID foreign key to quiz
        type: Task type discriminator (multiple_choice/free_text/cloze)
        prompt: The question or instruction text
        topic_detail: Specific topic or subtopic for this task
        order_index: Position of task within quiz (0-indexed)

    Relationships:
        quiz: Many-to-one relationship to Quiz
    """

    __tablename__ = "task"

    task_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz.quiz_id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to quiz",
    )

    quiz_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_version.quiz_version_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to quiz version",
    )

    type: Mapped[TaskType] = mapped_column(
        SQLEnum(TaskType, native_enum=False, length=20),
        nullable=False,
        comment="Task type discriminator",
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question or instruction text",
    )

    topic_detail: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Specific topic or subtopic",
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position within quiz (0-indexed)",
    )

    # Polymorphic setup for joined table inheritance
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": None,  # Abstract base, no direct instances
    }

    # Relationship to quiz
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="tasks",
    )

    version: Mapped["QuizVersion"] = relationship(
        "QuizVersion",
        back_populates="tasks",
    )

    # Composite index for efficient ordered queries (per version)
    __table_args__ = (
        Index("ix_task_quiz_version_order", "quiz_version_id", "order_index"),
        Index("ix_task_quiz_id", "quiz_id"),
    )


class MultipleChoiceTask(Task):
    """
    Multiple choice task with options.

    Extends Task with a separate table linked via task_id.
    No additional fields, but has relationship to options.

    Attributes:
        task_id: UUID primary key and foreign key to task.task_id

    Relationships:
        options: One-to-many relationship to TaskMultipleChoiceOption
    """

    __tablename__ = "task_multiple_choice"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task.task_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base task",
    )

    __mapper_args__ = {
        "polymorphic_identity": TaskType.MULTIPLE_CHOICE,
    }

    # Relationship to options
    options: Mapped[list["TaskMultipleChoiceOption"]] = relationship(
        "TaskMultipleChoiceOption",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MultipleChoiceTask(task_id={self.task_id}, "
            f"prompt='{self.prompt[:30]}...', "
            f"options_count={len(self.options) if self.options else 0})>"
        )


class TaskMultipleChoiceOption(Base):
    """
    Option for multiple choice task.

    Represents a single answer option with correctness flag and explanation.

    Attributes:
        option_id: UUID primary key
        task_id: UUID foreign key to task_multiple_choice
        text: Option text
        is_correct: Whether this option is correct
        explanation: Optional explanation for this option

    Relationships:
        task: Many-to-one relationship to MultipleChoiceTask
    """

    __tablename__ = "task_multiple_choice_option"

    option_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_multiple_choice.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to multiple choice task",
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Option text",
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Whether this option is correct",
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional explanation for this option",
    )

    # Relationship back to task
    task: Mapped["MultipleChoiceTask"] = relationship(
        "MultipleChoiceTask",
        back_populates="options",
    )


class FreeTextTask(Task):
    """
    Free text task with reference answer.

    Extends Task with reference answer field for LLM-based evaluation.

    Attributes:
        task_id: UUID primary key and foreign key to task.task_id
        reference_answer: Model answer for evaluation comparison
    """

    __tablename__ = "task_free_text"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task.task_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base task",
    )

    reference_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Model answer for evaluation comparison",
    )

    __mapper_args__ = {
        "polymorphic_identity": TaskType.FREE_TEXT,
    }


class ClozeTask(Task):
    """
    Cloze (fill-in-the-blank) task.

    Extends Task with template text containing placeholders and blanks to fill.

    Attributes:
        task_id: UUID primary key and foreign key to task.task_id
        template_text: Text with placeholders like {{blank_0}}, {{blank_1}}

    Relationships:
        blanks: One-to-many relationship to TaskClozeBlank
    """

    __tablename__ = "task_cloze"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task.task_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to base task",
    )

    template_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Text with placeholders like {{blank_0}}, {{blank_1}}",
    )

    __mapper_args__ = {
        "polymorphic_identity": TaskType.CLOZE,
    }

    # Relationship to blanks
    blanks: Mapped[list["TaskClozeBlank"]] = relationship(
        "TaskClozeBlank",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskClozeBlank.position",
    )

    def __repr__(self) -> str:
        return (
            f"<ClozeTask(task_id={self.task_id}, "
            f"prompt='{self.prompt[:30]}...', "
            f"blanks_count={len(self.blanks) if self.blanks else 0})>"
        )


class TaskClozeBlank(Base):
    """
    Blank (placeholder) for cloze task.

    Represents a single blank to be filled in with expected value.

    Attributes:
        blank_id: UUID primary key
        task_id: UUID foreign key to task_cloze
        position: Position/index of blank in template (0-indexed)
        expected_value: Expected answer for this blank

    Relationships:
        task: Many-to-one relationship to ClozeTask
    """

    __tablename__ = "task_cloze_blank"

    blank_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key",
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_cloze.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to cloze task",
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position/index of blank in template (0-indexed)",
    )

    expected_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Expected answer for this blank",
    )

    # Relationship back to task
    task: Mapped["ClozeTask"] = relationship(
        "ClozeTask",
        back_populates="blanks",
    )
