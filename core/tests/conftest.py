import uuid
import pytest
from django.utils import timezone

from core.models import Executor, Task


@pytest.fixture
def sample_executor(db):
    """
    Create and return a sample Executor instance for testing.

    Returns:
        Executor: An executor with name 'Test-Executor' and max_tasks=5
    """
    executor = Executor.objects.create(name="Test-Executor", max_tasks=5)
    return executor


@pytest.fixture
def sample_task(db):
    """
    Create and return a sample Task instance for testing.

    Returns:
        Task: A pending task with medium priority
    """
    task = Task.objects.create(
        description="Sample test task",
        priority=Task.Priority.MEDIUM,
        status=Task.Status.PENDING,
    )
    return task


@pytest.fixture
def sample_task_with_executor(db, sample_executor):
    """
    Create and return a Task instance assigned to an executor.

    Args:
        sample_executor: The executor fixture to assign the task to

    Returns:
        Task: An in-progress task assigned to the sample executor
    """
    task = Task.objects.create(
        description="Task assigned to executor",
        priority=Task.Priority.HIGH,
        status=Task.Status.IN_PROGRESS,
        assignee=sample_executor,
    )
    return task


@pytest.fixture
def multiple_executors(db):
    """
    Create and return multiple Executor instances for testing.

    Returns:
        list[Executor]: A list of 3 executors with varying capacities
    """
    executors = [
        Executor.objects.create(name="Executor-1", max_tasks=5),
        Executor.objects.create(name="Executor-2", max_tasks=3),
        Executor.objects.create(name="Executor-3", max_tasks=10),
    ]
    return executors


@pytest.fixture
def multiple_tasks(db):
    """
    Create and return multiple Task instances with different priorities.

    Returns:
        list[Task]: A list of 5 tasks with varying priorities and statuses
    """
    tasks = [
        Task.objects.create(
            description="High priority task 1",
            priority=Task.Priority.HIGHEST,
            status=Task.Status.PENDING,
        ),
        Task.objects.create(
            description="High priority task 2",
            priority=Task.Priority.HIGH,
            status=Task.Status.PENDING,
        ),
        Task.objects.create(
            description="Medium priority task",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
        ),
        Task.objects.create(
            description="Low priority task",
            priority=Task.Priority.LOW,
            status=Task.Status.PENDING,
        ),
        Task.objects.create(
            description="Completed task",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.COMPLETED,
            completed_at=timezone.now(),
        ),
    ]
    return tasks


@pytest.fixture
def completed_task(db, sample_executor):
    """
    Create and return a completed Task instance.

    Args:
        sample_executor: The executor fixture

    Returns:
        Task: A completed task with completed_at timestamp
    """
    task = Task.objects.create(
        description="Completed test task",
        priority=Task.Priority.MEDIUM,
        status=Task.Status.COMPLETED,
        assignee=sample_executor,
        completed_at=timezone.now(),
    )
    return task
