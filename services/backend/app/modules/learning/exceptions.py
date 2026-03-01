"""Learning module exceptions."""


class LearningModuleException(Exception):
    """Base exception for learning module."""

    pass


class AttemptNotFoundException(LearningModuleException):
    """Raised when attempt is not found."""

    def __init__(self, attempt_id: str):
        self.attempt_id = attempt_id
        super().__init__(f"Attempt not found: {attempt_id}")


class AttemptLockedException(LearningModuleException):
    """Raised when attempt is already evaluated and locked."""

    def __init__(self, attempt_id: str):
        self.attempt_id = attempt_id
        super().__init__(f"Attempt is locked (already evaluated): {attempt_id}")


class QuizNotFoundException(LearningModuleException):
    """Raised when quiz is not found."""

    def __init__(self, quiz_id: str):
        self.quiz_id = quiz_id
        super().__init__(f"Quiz not found: {quiz_id}")


class QuizNotCompletedException(LearningModuleException):
    """Raised when quiz is not in completed status."""

    def __init__(self, quiz_id: str):
        self.quiz_id = quiz_id
        super().__init__(f"Quiz not in completed status: {quiz_id}")


class AccessDeniedException(LearningModuleException):
    """Raised when user has no access to quiz."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message)


class TaskNotFoundException(LearningModuleException):
    """Raised when task is not found or doesn't belong to quiz."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class AnswerTypeMismatchException(LearningModuleException):
    """Raised when answer type doesn't match task type."""

    def __init__(self, expected: str, got: str):
        self.expected = expected
        self.got = got
        super().__init__(f"Answer type mismatch: expected {expected}, got {got}")


class AnswerNotFoundException(LearningModuleException):
    """Raised when answer is not found."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Answer not found for task: {task_id}")


class InvalidAnswerTypeException(LearningModuleException):
    """Raised when trying to perform operation on wrong answer type."""

    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected answer type {expected}, but got {actual}")
