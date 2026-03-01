"""Unit tests for TaskRepository with focus on polymorphic inheritance."""

import uuid

import pytest

from datetime import datetime, timezone

from app.modules.quiz.models.quiz import Quiz, QuizState, QuizStatus
from app.modules.quiz.models.quiz_version import QuizVersion, QuizVersionStatus
from app.modules.quiz.models.task import (
    Task,
    MultipleChoiceTask,
    FreeTextTask,
    ClozeTask,
    TaskType,
)
from app.modules.quiz.schemas import (
    MultipleChoiceTaskCreate,
    MultipleChoiceOptionCreate,
    FreeTextTaskCreate,
    ClozeTaskCreate,
    ClozeBlankCreate,
    TaskUpsertDto,
)
from app.modules.quiz.repositories.task_repository import TaskRepository
from app.modules.quiz.strategies import TaskMappingRegistry, task_mapping_registry


pytestmark = pytest.mark.unit


async def _save_task(
    repository: TaskRepository,
    mapping_registry: TaskMappingRegistry,
    quiz_id: uuid.UUID,
    quiz_version_id: uuid.UUID,
    task_input: TaskUpsertDto,
    order_index: int,
):
    task_model = mapping_registry.get(task_input.type).build_model(
        quiz_id,
        quiz_version_id,
        task_input,
        order_index,
    )
    return await repository.save(task_model)


class TestTaskRepositoryPolymorphism:
    """Test suite for TaskRepository polymorphic behavior."""

    @pytest.fixture
    async def quiz(self, db_session):
        """Create a quiz for testing tasks."""
        quiz = Quiz(
            title="Test Quiz",
            topic="Testing",
            created_by=uuid.uuid4(),
            state=QuizState.PRIVATE,
            status=QuizStatus.PENDING,
        )
        db_session.add(quiz)
        await db_session.flush()

        version_id = uuid.uuid4()
        version = QuizVersion(
            quiz_id=quiz.quiz_id,
            quiz_version_id=version_id,
            created_by=quiz.created_by,
            status=QuizVersionStatus.PUBLISHED,
            version_number=1,
            is_current=True,
            created_at=datetime.now(timezone.utc),
            committed_at=datetime.now(timezone.utc),
        )
        db_session.add(version)
        await db_session.flush()
        await db_session.refresh(quiz)
        quiz.current_version_id = version_id
        return quiz

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return TaskRepository(db_session)

    @pytest.fixture
    def mapping_registry(self) -> TaskMappingRegistry:
        """Create a mapping registry for test tasks."""
        return task_mapping_registry()

    # ==================== Polymorphism Tests ====================

    async def test_get_by_id_returns_multiple_choice_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_id returns MultipleChoiceTask instance for MC tasks."""
        # Arrange
        options = [
            MultipleChoiceOptionCreate(
                text="Option A",
                is_correct=True,
                explanation="Correct!",
            ),
            MultipleChoiceOptionCreate(
                text="Option B",
                is_correct=False,
                explanation=None,
            ),
        ]
        task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="What is the answer?",
            topic_detail="Test topic",
            options=options,
        )
        created_task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Act
        result = await repository.get_by_id(created_task.task_id)

        # Assert - Polymorphism check
        assert result is not None
        assert isinstance(result, MultipleChoiceTask)
        assert isinstance(result, Task)  # Also a Task
        assert result.type == TaskType.MULTIPLE_CHOICE
        assert hasattr(result, "options")

    async def test_get_by_id_returns_free_text_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_id returns FreeTextTask instance for free text tasks."""
        # Arrange
        task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Explain polymorphism",
            topic_detail="OOP concepts",
            reference_answer="Polymorphism allows objects to be treated as instances...",
        )
        created_task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Act
        result = await repository.get_by_id(created_task.task_id)

        # Assert - Polymorphism check
        assert result is not None
        assert isinstance(result, FreeTextTask)
        assert isinstance(result, Task)
        assert result.type == TaskType.FREE_TEXT
        assert hasattr(result, "reference_answer")
        assert (
            result.reference_answer
            == "Polymorphism allows objects to be treated as instances..."
        )

    async def test_get_by_id_returns_cloze_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_id returns ClozeTask instance for cloze tasks."""
        # Arrange
        blanks = [
            ClozeBlankCreate(position=1, expected_value="Paris"),
            ClozeBlankCreate(position=2, expected_value="France"),
        ]
        task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Fill in the blanks",
            topic_detail="Geography",
            template_text="The capital of {{blank_2}} is {{blank_1}}",
            blanks=blanks,
        )
        created_task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Act
        result = await repository.get_by_id(created_task.task_id)

        # Assert - Polymorphism check
        assert result is not None
        assert isinstance(result, ClozeTask)
        assert isinstance(result, Task)
        assert result.type == TaskType.CLOZE
        assert hasattr(result, "template_text")
        assert hasattr(result, "blanks")

    async def test_get_by_quiz_version_returns_mixed_task_types(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_quiz_version returns correct subtypes for mixed tasks."""
        # Arrange - Create one of each type
        mc_task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="MC Question",
            topic_detail="Topic 1",
            options=[
                MultipleChoiceOptionCreate(text="A", is_correct=True, explanation=None),
            ],
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=mc_task_input,
            order_index=0,
        )

        ft_task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="FT Question",
            topic_detail="Topic 2",
            reference_answer="Reference",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=ft_task_input,
            order_index=1,
        )

        cloze_task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Cloze Question",
            topic_detail="Topic 3",
            template_text="The {{blank_1}} is blue",
            blanks=[ClozeBlankCreate(position=1, expected_value="sky")],
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=cloze_task_input,
            order_index=2,
        )
        await db_session.commit()

        # Act
        tasks = await repository.get_by_quiz_version(quiz.current_version_id)

        # Assert - Each task has correct type
        assert len(tasks) == 3

        # Verify order
        assert tasks[0].order_index == 0
        assert tasks[1].order_index == 1
        assert tasks[2].order_index == 2

        # Verify polymorphism - each is the correct subtype
        assert isinstance(tasks[0], MultipleChoiceTask)
        assert isinstance(tasks[1], FreeTextTask)
        assert isinstance(tasks[2], ClozeTask)

        # Verify type discriminator
        assert tasks[0].type == TaskType.MULTIPLE_CHOICE
        assert tasks[1].type == TaskType.FREE_TEXT
        assert tasks[2].type == TaskType.CLOZE

    async def test_isinstance_check_works_for_type_specific_logic(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that isinstance checks work for type-specific processing."""
        # Arrange
        mc_task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="MC",
            topic_detail="Topic",
            options=[
                MultipleChoiceOptionCreate(text="A", is_correct=True, explanation=None),
            ],
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=mc_task_input,
            order_index=0,
        )

        ft_task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="FT",
            topic_detail="Topic",
            reference_answer="Ref",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=ft_task_input,
            order_index=1,
        )
        await db_session.commit()

        # Act
        tasks = await repository.get_by_quiz_version(quiz.current_version_id)

        # Assert - isinstance works for conditional logic
        mc_count = sum(1 for t in tasks if isinstance(t, MultipleChoiceTask))
        ft_count = sum(1 for t in tasks if isinstance(t, FreeTextTask))
        cloze_count = sum(1 for t in tasks if isinstance(t, ClozeTask))

        assert mc_count == 1
        assert ft_count == 1
        assert cloze_count == 0

    # ==================== Eager Loading Tests ====================

    async def test_multiple_choice_options_are_eager_loaded(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that MultipleChoiceTask options are eagerly loaded."""
        # Arrange
        options = [
            MultipleChoiceOptionCreate(
                text="Option A",
                is_correct=True,
                explanation="Correct!",
            ),
            MultipleChoiceOptionCreate(
                text="Option B",
                is_correct=False,
                explanation=None,
            ),
            MultipleChoiceOptionCreate(
                text="Option C",
                is_correct=False,
                explanation=None,
            ),
        ]
        task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="Question with options",
            topic_detail="Topic",
            options=options,
        )
        created_task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Act
        result = await repository.get_by_id(created_task.task_id)

        # Assert - Options are loaded without additional query
        assert result.options is not None
        assert len(result.options) == 3
        assert result.options[0].text == "Option A"
        assert result.options[0].is_correct is True
        assert result.options[0].explanation == "Correct!"

    async def test_cloze_blanks_are_eager_loaded(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that ClozeTask blanks are eagerly loaded."""
        # Arrange
        blanks = [
            ClozeBlankCreate(position=1, expected_value="Python"),
            ClozeBlankCreate(position=2, expected_value="programming"),
        ]
        task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Fill in",
            topic_detail="Topic",
            template_text="{{blank_1}} is a {{blank_2}} language",
            blanks=blanks,
        )
        created_task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Act
        result = await repository.get_by_id(created_task.task_id)

        # Assert - Blanks are loaded without additional query
        assert result.blanks is not None
        assert len(result.blanks) == 2

    async def test_get_by_quiz_version_eager_loads_nested_entities(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_quiz_version eagerly loads options and blanks for all tasks."""
        # Arrange
        mc_task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="MC",
            topic_detail="Topic",
            options=[
                MultipleChoiceOptionCreate(text="A", is_correct=True, explanation=None),
                MultipleChoiceOptionCreate(
                    text="B",
                    is_correct=False,
                    explanation=None,
                ),
            ],
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=mc_task_input,
            order_index=0,
        )

        cloze_task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Cloze",
            topic_detail="Topic",
            template_text="{{blank_1}}",
            blanks=[ClozeBlankCreate(position=1, expected_value="answer")],
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=cloze_task_input,
            order_index=1,
        )
        await db_session.commit()

        # Act
        tasks = await repository.get_by_quiz_version(quiz.current_version_id)

        # Assert - All nested entities loaded
        mc_task = tasks[0]
        cloze_task = tasks[1]

        assert isinstance(mc_task, MultipleChoiceTask)
        assert len(mc_task.options) == 2

        assert isinstance(cloze_task, ClozeTask)
        assert len(cloze_task.blanks) == 1

    # ==================== CRUD Tests ====================

    async def test_create_multiple_choice_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test creating a multiple choice task with options."""
        # Arrange
        options = [
            MultipleChoiceOptionCreate(
                text="Paris",
                is_correct=True,
                explanation="Capital of France",
            ),
            MultipleChoiceOptionCreate(
                text="London",
                is_correct=False,
                explanation=None,
            ),
            MultipleChoiceOptionCreate(
                text="Berlin",
                is_correct=False,
                explanation=None,
            ),
        ]

        # Act
        task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="What is the capital of France?",
            topic_detail="European Capitals",
            options=options,
        )
        task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Assert
        assert task is not None
        assert isinstance(task.task_id, uuid.UUID)
        assert task.quiz_id == quiz.quiz_id
        assert task.prompt == "What is the capital of France?"
        assert task.topic_detail == "European Capitals"
        assert task.order_index == 0
        assert len(task.options) == 3

    async def test_create_free_text_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test creating a free text task."""
        # Act
        task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Explain the concept of inheritance in OOP",
            topic_detail="Object-Oriented Programming",
            reference_answer="Inheritance is a mechanism that allows a class to inherit properties...",
        )
        task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Assert
        assert task is not None
        assert isinstance(task.task_id, uuid.UUID)
        assert task.prompt == "Explain the concept of inheritance in OOP"
        assert task.reference_answer.startswith("Inheritance is a mechanism")

    async def test_create_cloze_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test creating a cloze task with blanks."""
        # Arrange
        blanks = [
            ClozeBlankCreate(position=1, expected_value="Paris"),
        ]

        # Act
        task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Fill in the capital city",
            topic_detail="Geography",
            template_text="The capital of France is {{blank_1}}",
            blanks=blanks,
        )
        task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()

        # Assert
        assert task is not None
        assert task.template_text == "The capital of France is {{blank_1}}"
        assert len(task.blanks) == 1
        assert task.blanks[0].expected_value == "Paris"

    async def test_delete_task_cascades_to_options(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that deleting a MultipleChoiceTask cascades to its options."""
        # Arrange
        task_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="Question",
            topic_detail="Topic",
            options=[
                MultipleChoiceOptionCreate(text="A", is_correct=True, explanation=None),
                MultipleChoiceOptionCreate(
                    text="B",
                    is_correct=False,
                    explanation=None,
                ),
            ],
        )
        task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()
        task_id = task.task_id

        # Act
        result = await repository.delete(task_id)
        await db_session.commit()

        # Assert
        assert result is True
        deleted_task = await repository.get_by_id(task_id)
        assert deleted_task is None

    async def test_delete_task_cascades_to_blanks(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that deleting a ClozeTask cascades to its blanks."""
        # Arrange
        task_input = ClozeTaskCreate(
            type="cloze",
            prompt="Fill in",
            topic_detail="Topic",
            template_text="{{blank_1}} {{blank_2}}",
            blanks=[
                ClozeBlankCreate(position=1, expected_value="Hello"),
                ClozeBlankCreate(position=2, expected_value="World"),
            ],
        )
        task = await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input,
            order_index=0,
        )
        await db_session.commit()
        task_id = task.task_id

        # Act
        result = await repository.delete(task_id)
        await db_session.commit()

        # Assert
        assert result is True
        deleted_task = await repository.get_by_id(task_id)
        assert deleted_task is None

    async def test_delete_nonexistent_task_returns_false(self, repository):
        """Test that deleting a non-existent task returns False."""
        # Act
        result = await repository.delete(uuid.uuid4())

        # Assert
        assert result is False

    async def test_get_by_id_not_found(self, repository):
        """Test that get_by_id returns None for non-existent task."""
        # Act
        result = await repository.get_by_id(uuid.uuid4())

        # Assert
        assert result is None

    async def test_get_by_quiz_version_empty(self, repository, quiz):
        """Test that get_by_quiz_version returns empty list for quiz version without tasks."""
        # Act
        tasks = await repository.get_by_quiz_version(quiz.current_version_id)

        # Assert
        assert tasks == []

    async def test_get_max_order_index_no_tasks(self, repository, quiz):
        """Test get_max_order_index returns -1 when no tasks exist."""
        # Act
        max_index = await repository.get_max_order_index(quiz.quiz_id)

        # Assert
        assert max_index == -1

    async def test_get_max_order_index_with_tasks(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test get_max_order_index returns correct value."""
        # Arrange
        task_input_1 = FreeTextTaskCreate(
            type="free_text",
            prompt="Q1",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input_1,
            order_index=0,
        )

        task_input_2 = FreeTextTaskCreate(
            type="free_text",
            prompt="Q2",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input_2,
            order_index=5,
        )

        task_input_3 = FreeTextTaskCreate(
            type="free_text",
            prompt="Q3",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=task_input_3,
            order_index=2,
        )
        await db_session.commit()

        # Act
        max_index = await repository.get_max_order_index(quiz.quiz_id)

        # Assert
        assert max_index == 5

    async def test_tasks_ordered_by_order_index(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """Test that get_by_quiz_version returns tasks ordered by order_index."""
        # Arrange - Create in non-sequential order
        third_task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Third",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=third_task_input,
            order_index=2,
        )

        first_task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="First",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=first_task_input,
            order_index=0,
        )

        second_task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Second",
            topic_detail="T",
            reference_answer="R",
        )
        await _save_task(
            repository=repository,
            mapping_registry=mapping_registry,
            quiz_id=quiz.quiz_id,
            quiz_version_id=quiz.current_version_id,
            task_input=second_task_input,
            order_index=1,
        )
        await db_session.commit()

        # Act
        tasks = await repository.get_by_quiz_version(quiz.current_version_id)

        # Assert
        assert len(tasks) == 3
        assert tasks[0].prompt == "First"
        assert tasks[1].prompt == "Second"
        assert tasks[2].prompt == "Third"
