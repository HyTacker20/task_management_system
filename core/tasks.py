from celery import shared_task
from django.db.models import Q

from core.models import Task
from core.services.distribution import distribute_pending_tasks
from core.services.scaling import adjust_executor_count


@shared_task
def run_system_tick():
    """
    Periodic task that runs the system tick to manage executors and distribute tasks.

    This task:
    1. Counts pending tasks in the queue
    2. Adjusts executor count based on pending task load
    3. Distributes pending tasks to available executors
    """

    # Get count of pending tasks
    pending_queue_count = Task.objects.filter(status=Task.Status.PENDING).count()

    # Adjust executor count based on pending queue
    adjust_executor_count(pending_queue_count)

    # Distribute pending tasks to available executors
    distribute_pending_tasks()

    return {
        "pending_tasks_processed": pending_queue_count,
        "message": "System tick completed successfully",
    }
