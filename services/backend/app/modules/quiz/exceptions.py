"""Domain-specific exceptions for the quiz module.
"""


class QuizModuleException(Exception):
    """Base exception for quiz module."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class QuizNotFoundException(QuizModuleException):
    """Raised when a quiz is not found."""

    def __init__(self, message: str = "Quiz not found"):
        super().__init__(message)


class TaskNotFoundException(QuizModuleException):
    """Raised when a task is not found."""

    def __init__(self, message: str = "Task not found"):
        super().__init__(message)


class AccessDeniedException(QuizModuleException):
    """Raised when user lacks permission to access a resource."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message)


class InvalidTaskTypeException(QuizModuleException):
    """Raised when an unknown or invalid task type is provided."""

    def __init__(self, task_type: str):
        super().__init__(f"Invalid task type: {task_type}")
        self.task_type = task_type


class TaskTypeMismatchException(QuizModuleException):
    """Raised when update DTO type doesn't match the task's actual type."""

    def __init__(self, expected_type: str, actual_type: str):
        super().__init__(
            f"Task type mismatch: task is '{expected_type}', "
            f"but update DTO is for '{actual_type}'",
        )
        self.expected_type = expected_type
        self.actual_type = actual_type


class EditSessionRequiredException(QuizModuleException):
    """Raised when an edit session id is required but missing."""

    def __init__(self, message: str = "Edit session id is required"):
        super().__init__(message)


class EditSessionNotFoundException(QuizModuleException):
    """Raised when an edit session is not found."""

    def __init__(self, message: str = "Edit session not found"):
        super().__init__(message)


class EditSessionInactiveException(QuizModuleException):
    """Raised when an edit session is inactive."""

    def __init__(self, message: str = "Edit session is not active"):
        super().__init__(message)


class EditSessionTaskMismatchException(QuizModuleException):
    """Raised when a task is not part of the active draft session."""

    def __init__(self, message: str = "Task does not belong to this edit session"):
        super().__init__(message)
