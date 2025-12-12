from django.db.models import Count, Q

from core.models import Executor, Task


def distribute_pending_tasks() -> None:
    """
    Distribute pending tasks to available executors based on their capacity.

    Logic:
    - Get pending tasks ordered by priority (1 is highest, 5 is lowest)
    - Iterate and assign to the Executor with the minimum active tasks
    - Skip if Executor is at max_tasks capacity
    """

    # Get all pending tasks ordered by priority (ascending, so 1 comes first)
    pending_tasks = Task.objects.filter(status=Task.Status.PENDING).order_by(
        "priority", "created_at"
    )

    if not pending_tasks.exists():
        return

    for task in pending_tasks:
        # Find the best executor to assign this task
        executor = _find_available_executor()

        if executor:
            # Assign task to executor and update status
            task.assignee = executor
            task.status = Task.Status.IN_PROGRESS
            task.save(update_fields=["assignee", "status"])


def _find_available_executor() -> Executor | None:
    """
    Find an executor with the minimum active tasks that hasn't reached capacity.

    Returns:
        Executor instance if available, None if all executors are at capacity
    """

    # Get all executors with their active task count
    executors = Executor.objects.annotate(
        active_task_count=Count(
            "tasks",
            filter=Q(tasks__status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]),
        )
    ).order_by("active_task_count")

    # Find the first executor that hasn't reached max capacity
    for executor in executors:
        if executor.active_task_count < executor.max_tasks:
            return executor

    # All executors are at capacity
    return None
