from django.db.models import Count, Q

from core.models import Executor, Task


def adjust_executor_count(pending_queue_count: int) -> None:
    """
    Automatically adjust the number of executors based on pending task count.

    Logic:
    - If pending > 10: Create a new Executor
    - If pending < 5: Reduce Executors to 2 (delete idle ones)

    Args:
        pending_queue_count: Number of pending tasks in the queue
    """

    if pending_queue_count > 10:
        # Scale up: Create a new executor
        _scale_up()
    elif pending_queue_count < 5:
        # Scale down: Reduce to 2 executors (delete idle ones)
        _scale_down()


def _scale_up() -> None:
    """Create a new executor with default configuration."""
    executor_count = Executor.objects.count()
    new_executor_name = f"Executor-{executor_count + 1}"

    # Check if executor with this name already exists
    if not Executor.objects.filter(name=new_executor_name).exists():
        Executor.objects.create(
            name=new_executor_name, max_tasks=5  # Default max_tasks value
        )


def _scale_down() -> None:
    """Reduce executors to 2 by removing idle ones."""
    current_executor_count = Executor.objects.count()

    # Only scale down if we have more than 2 executors
    if current_executor_count <= 2:
        return

    # Find idle executors (those with no active tasks)
    # Active tasks are those that are pending or in_progress
    executors_with_task_count = Executor.objects.annotate(
        active_task_count=Count(
            "tasks",
            filter=Q(tasks__status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]),
        )
    ).order_by("active_task_count", "name")

    # Calculate how many executors to remove
    executors_to_remove = current_executor_count - 2

    # Get idle executors (with 0 active tasks) to remove
    idle_executors = executors_with_task_count.filter(active_task_count=0)[
        :executors_to_remove
    ]

    # If we don't have enough idle executors, get executors with least tasks
    if idle_executors.count() < executors_to_remove:
        executors_to_delete = executors_with_task_count[:executors_to_remove]
    else:
        executors_to_delete = idle_executors

    # Delete the selected executors
    for executor in executors_to_delete:
        executor.delete()
