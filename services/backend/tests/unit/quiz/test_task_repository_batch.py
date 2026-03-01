"""Unit tests for TaskRepository.get_by_ids."""

import uuid

import pytest

from datetime import datetime, timezone

from app.modules.quiz.models.quiz import Quiz, QuizState, QuizStatus
from app.modules.quiz.models.quiz_version import QuizVersion, QuizVersionStatus
from app.modules.quiz.models.task import (
    MultipleChoiceTask,
    FreeTextTask,
    ClozeTask,
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


class TestTaskRepositoryGetByIds:
    """Test suite for TaskRepository.get_by_ids."""

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
        return TaskRepository(db_session)

    @pytest.fixture
    def mapping_registry(self) -> TaskMappingRegistry:
        return task_mapping_registry()

    async def test_empty_list_returns_empty(self, repository):
        result = await repository.get_by_ids([])
        assert result == []

    async def test_nonexistent_ids_returns_empty(self, repository):
        result = await repository.get_by_ids([uuid.uuid4(), uuid.uuid4()])
        assert result == []

    async def test_returns_single_task(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Explain testing",
            topic_detail="QA",
            reference_answer="Testing ensures software quality.",
        )
        created = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            task_input,
            0,
        )
        await db_session.commit()

        result = await repository.get_by_ids([created.task_id])

        assert len(result) == 1
        assert result[0].task_id == created.task_id
        assert isinstance(result[0], FreeTextTask)

    async def test_returns_multiple_mixed_types(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        mc_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="MC Question",
            topic_detail="Topic",
            options=[
                MultipleChoiceOptionCreate(
                    text="A",
                    is_correct=True,
                    explanation=None,
                ),
            ],
        )
        mc_task = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            mc_input,
            0,
        )

        ft_input = FreeTextTaskCreate(
            type="free_text",
            prompt="FT Question",
            topic_detail="Topic",
            reference_answer="Answer",
        )
        ft_task = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            ft_input,
            1,
        )

        cloze_input = ClozeTaskCreate(
            type="cloze",
            prompt="Cloze Question",
            topic_detail="Topic",
            template_text="The {{blank_1}} is blue",
            blanks=[ClozeBlankCreate(position=1, expected_value="sky")],
        )
        cloze_task = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            cloze_input,
            2,
        )
        await db_session.commit()

        result = await repository.get_by_ids(
            [mc_task.task_id, ft_task.task_id, cloze_task.task_id],
        )

        assert len(result) == 3
        types = {type(t) for t in result}
        assert types == {MultipleChoiceTask, FreeTextTask, ClozeTask}

    async def test_eager_loads_mc_options(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        mc_input = MultipleChoiceTaskCreate(
            type="multiple_choice",
            prompt="MC",
            topic_detail="T",
            options=[
                MultipleChoiceOptionCreate(
                    text="Opt A",
                    is_correct=True,
                    explanation="Yes",
                ),
                MultipleChoiceOptionCreate(
                    text="Opt B",
                    is_correct=False,
                    explanation=None,
                ),
            ],
        )
        task = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            mc_input,
            0,
        )
        await db_session.commit()

        result = await repository.get_by_ids([task.task_id])

        assert len(result) == 1
        assert isinstance(result[0], MultipleChoiceTask)
        assert len(result[0].options) == 2

    async def test_eager_loads_cloze_blanks(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        cloze_input = ClozeTaskCreate(
            type="cloze",
            prompt="Fill in",
            topic_detail="T",
            template_text="{{blank_1}} and {{blank_2}}",
            blanks=[
                ClozeBlankCreate(position=1, expected_value="Hello"),
                ClozeBlankCreate(position=2, expected_value="World"),
            ],
        )
        task = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            cloze_input,
            0,
        )
        await db_session.commit()

        result = await repository.get_by_ids([task.task_id])

        assert len(result) == 1
        assert isinstance(result[0], ClozeTask)
        assert len(result[0].blanks) == 2

    async def test_ignores_nonexistent_ids_in_mixed_input(
        self,
        repository,
        quiz,
        db_session,
        mapping_registry,
    ):
        """When some IDs exist and some don't, only existing tasks are returned."""
        task_input = FreeTextTaskCreate(
            type="free_text",
            prompt="Q",
            topic_detail="T",
            reference_answer="A",
        )
        created = await _save_task(
            repository,
            mapping_registry,
            quiz.quiz_id,
            quiz.current_version_id,
            task_input,
            0,
        )
        await db_session.commit()

        result = await repository.get_by_ids(
            [created.task_id, uuid.uuid4(), uuid.uuid4()],
        )

        assert len(result) == 1
        assert result[0].task_id == created.task_id
