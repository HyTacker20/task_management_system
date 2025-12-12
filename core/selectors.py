from django.db.models import Count, Q
from core.models import Executor, Task


def get_global_stats() -> dict:
    """
    Get global statistics of tasks grouped by status.

    Returns:
        Dictionary with task counts by status:
        {
            'pending': int,
            'in_progress': int,
            'completed': int,
            'total': int
        }
    """

    # Count tasks by status
    pending_count = Task.objects.filter(status=Task.Status.PENDING).count()
    in_progress_count = Task.objects.filter(status=Task.Status.IN_PROGRESS).count()
    completed_count = Task.objects.filter(status=Task.Status.COMPLETED).count()
    total_count = Task.objects.count()

    return {
        "pending": pending_count,
        "in_progress": in_progress_count,
        "completed": completed_count,
        "total": total_count,
    }


def get_executor_stats() -> list[dict]:
    """
    Get statistics for all executors with their current task load.

    Returns:
        List of dictionaries containing executor information:
        [
            {
                'id': int,
                'name': str,
                'max_tasks': int,
                'active_tasks': int,
                'pending_tasks': int,
                'in_progress_tasks': int,
                'completed_tasks': int
            },
            ...
        ]
    """

    # Get all executors with annotated task counts
    executors = Executor.objects.annotate(
        active_tasks=Count(
            "tasks",
            filter=Q(tasks__status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]),
        ),
        pending_tasks=Count("tasks", filter=Q(tasks__status=Task.Status.PENDING)),
        in_progress_tasks=Count(
            "tasks", filter=Q(tasks__status=Task.Status.IN_PROGRESS)
        ),
        completed_tasks=Count("tasks", filter=Q(tasks__status=Task.Status.COMPLETED)),
    ).order_by("name")

    # Convert to list of dictionaries
    executor_stats = []
    for executor in executors:
        executor_stats.append(
            {
                "id": executor.id,
                "name": executor.name,
                "max_tasks": executor.max_tasks,
                "active_tasks": executor.active_tasks,
                "pending_tasks": executor.pending_tasks,
                "in_progress_tasks": executor.in_progress_tasks,
                "completed_tasks": executor.completed_tasks,
            }
        )

    return executor_stats
