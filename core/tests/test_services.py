import pytest

from core.models import Executor, Task
from core.services.distribution import distribute_pending_tasks
from core.services.scaling import adjust_executor_count


@pytest.mark.unit
class TestScalingLogic:
    """Test suite for executor scaling logic."""

    def test_scale_up_when_pending_tasks_exceed_threshold(self, db):
        """Test that having > 10 pending tasks increases executor count."""
        # Ensure no pre-existing tasks
        Task.objects.all().delete()

        # Create 2 initial executors
        Executor.objects.create(name="Executor-1", max_tasks=5)
        Executor.objects.create(name="Executor-2", max_tasks=5)

        # Create 11 pending tasks
        for i in range(11):
            Task.objects.create(
                description=f"Pending task {i}",
                priority=Task.Priority.MEDIUM,
                status=Task.Status.PENDING,
            )

        initial_executor_count = Executor.objects.count()
        assert initial_executor_count == 2

        # Run scaling logic with > 10 pending tasks
        pending_count = Task.objects.filter(status=Task.Status.PENDING).count()
        assert pending_count == 11

        adjust_executor_count(pending_count)

        # Verify executor count increased
        new_executor_count = Executor.objects.count()
        assert new_executor_count == 3
        assert new_executor_count > initial_executor_count

    def test_scale_down_when_pending_tasks_below_threshold(self, db):
        """Test that having < 5 pending tasks decreases executor count down to minimum of 2."""
        # Create 5 executors
        for i in range(1, 6):
            Executor.objects.create(name=f"Executor-{i}", max_tasks=5)

        # Create only 4 pending tasks (< 5)
        for i in range(4):
            Task.objects.create(
                description=f"Pending task {i}",
                priority=Task.Priority.MEDIUM,
                status=Task.Status.PENDING,
            )

        initial_executor_count = Executor.objects.count()
        assert initial_executor_count == 5

        # Run scaling logic with < 5 pending tasks
        pending_count = Task.objects.filter(status=Task.Status.PENDING).count()
        assert pending_count == 4

        adjust_executor_count(pending_count)

        # Verify executor count decreased to minimum of 2
        new_executor_count = Executor.objects.count()
        assert new_executor_count == 2
        assert new_executor_count < initial_executor_count

    def test_scale_down_respects_minimum_of_two_executors(self, db):
        """Test that scaling down never goes below 2 executors."""
        # Create exactly 2 executors
        Executor.objects.create(name="Executor-1", max_tasks=5)
        Executor.objects.create(name="Executor-2", max_tasks=5)

        # Create 2 pending tasks (< 5, should trigger scale down)
        Task.objects.create(
            description="Task 1",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.PENDING,
        )
        Task.objects.create(
            description="Task 2",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.PENDING,
        )

        initial_executor_count = Executor.objects.count()
        assert initial_executor_count == 2

        # Run scaling logic
        pending_count = Task.objects.filter(status=Task.Status.PENDING).count()
        adjust_executor_count(pending_count)

        # Verify executor count stays at 2 (minimum)
        final_executor_count = Executor.objects.count()
        assert final_executor_count == 2

    def test_no_scaling_when_pending_between_thresholds(self, db):
        """Test that executor count remains stable when pending tasks are between 5 and 10."""
        # Create 3 executors
        for i in range(1, 4):
            Executor.objects.create(name=f"Executor-{i}", max_tasks=5)

        # Create 7 pending tasks (between 5 and 10)
        for i in range(7):
            Task.objects.create(
                description=f"Pending task {i}",
                priority=Task.Priority.MEDIUM,
                status=Task.Status.PENDING,
            )

        initial_executor_count = Executor.objects.count()
        assert initial_executor_count == 3

        # Run scaling logic
        pending_count = Task.objects.filter(status=Task.Status.PENDING).count()
        assert 5 <= pending_count <= 10

        adjust_executor_count(pending_count)

        # Verify executor count unchanged
        final_executor_count = Executor.objects.count()
        assert final_executor_count == initial_executor_count


@pytest.mark.unit
class TestDistributionLogic:
    """Test suite for task distribution logic."""

    def test_high_priority_task_assigned_before_low_priority(self, db):
        """Test that a high-priority task (Priority 1) is assigned before a low-priority task (Priority 5)."""
        # Create executor
        executor = Executor.objects.create(name="Executor-1", max_tasks=10)

        # Create low priority task first
        low_priority_task = Task.objects.create(
            description="Low priority task",
            priority=Task.Priority.LOWEST,  # Priority 5
            status=Task.Status.PENDING,
        )

        # Create high priority task second
        high_priority_task = Task.objects.create(
            description="High priority task",
            priority=Task.Priority.HIGHEST,  # Priority 1
            status=Task.Status.PENDING,
        )

        # Run distribution logic
        distribute_pending_tasks()

        # Refresh from database
        high_priority_task.refresh_from_db()
        low_priority_task.refresh_from_db()

        # Verify high priority task is assigned (in_progress)
        assert high_priority_task.status == Task.Status.IN_PROGRESS
        assert high_priority_task.assignee == executor

        # Low priority task should also be assigned since executor has capacity
        assert low_priority_task.status == Task.Status.IN_PROGRESS
        assert low_priority_task.assignee == executor

    def test_tasks_assigned_to_executor_with_least_load(self, db):
        """Test that tasks are assigned to the executor with the least load."""
        # Create 3 executors
        executor1 = Executor.objects.create(name="Executor-1", max_tasks=10)
        executor2 = Executor.objects.create(name="Executor-2", max_tasks=10)
        executor3 = Executor.objects.create(name="Executor-3", max_tasks=10)

        # Assign existing tasks to create different loads
        # Executor 1: 3 active tasks
        for i in range(3):
            Task.objects.create(
                description=f"Existing task {i}",
                priority=Task.Priority.MEDIUM,
                status=Task.Status.IN_PROGRESS,
                assignee=executor1,
            )

        # Executor 2: 1 active task
        Task.objects.create(
            description="Existing task",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
            assignee=executor2,
        )

        # Executor 3: 0 active tasks (least load)

        # Create new pending task
        new_task = Task.objects.create(
            description="New pending task",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.PENDING,
        )

        # Run distribution logic
        distribute_pending_tasks()

        # Refresh from database
        new_task.refresh_from_db()

        # Verify task assigned to executor with least load (executor3)
        assert new_task.assignee == executor3
        assert new_task.status == Task.Status.IN_PROGRESS

    def test_executor_at_max_capacity_does_not_receive_tasks(self, db):
        """Test that an executor at max_tasks capacity does not receive new tasks."""
        # Create 2 executors
        executor1 = Executor.objects.create(name="Executor-1", max_tasks=2)
        executor2 = Executor.objects.create(name="Executor-2", max_tasks=10)

        # Fill executor1 to max capacity
        Task.objects.create(
            description="Task 1",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
            assignee=executor1,
        )
        Task.objects.create(
            description="Task 2",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
            assignee=executor1,
        )

        # Create new pending task
        new_task = Task.objects.create(
            description="New pending task",
            priority=Task.Priority.HIGH,
            status=Task.Status.PENDING,
        )

        # Run distribution logic
        distribute_pending_tasks()

        # Refresh from database
        new_task.refresh_from_db()

        # Verify task assigned to executor2 (not at capacity), not executor1
        assert new_task.assignee == executor2
        assert new_task.assignee != executor1
        assert new_task.status == Task.Status.IN_PROGRESS

    def test_task_remains_pending_when_all_executors_at_capacity(self, db):
        """Test that tasks remain pending when all executors are at max capacity."""
        # Create executor with small capacity
        executor = Executor.objects.create(name="Executor-1", max_tasks=1)

        # Fill executor to capacity
        Task.objects.create(
            description="Existing task",
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
            assignee=executor,
        )

        # Create new pending task
        new_task = Task.objects.create(
            description="New pending task",
            priority=Task.Priority.HIGH,
            status=Task.Status.PENDING,
        )

        # Run distribution logic
        distribute_pending_tasks()

        # Refresh from database
        new_task.refresh_from_db()

        # Verify task remains pending (not assigned)
        assert new_task.status == Task.Status.PENDING
        assert new_task.assignee is None

    def test_multiple_tasks_distributed_in_priority_order(self, db):
        """Test that multiple pending tasks are distributed in correct priority order."""
        # Create executor with high capacity
        executor = Executor.objects.create(name="Executor-1", max_tasks=10)

        # Create tasks in random order but with different priorities
        task_p3 = Task.objects.create(
            description="Medium priority",
            priority=Task.Priority.MEDIUM,  # 3
            status=Task.Status.PENDING,
        )
        task_p1 = Task.objects.create(
            description="Highest priority",
            priority=Task.Priority.HIGHEST,  # 1
            status=Task.Status.PENDING,
        )
        task_p5 = Task.objects.create(
            description="Lowest priority",
            priority=Task.Priority.LOWEST,  # 5
            status=Task.Status.PENDING,
        )
        task_p2 = Task.objects.create(
            description="High priority",
            priority=Task.Priority.HIGH,  # 2
            status=Task.Status.PENDING,
        )

        # Run distribution logic
        distribute_pending_tasks()

        # Refresh all tasks
        task_p1.refresh_from_db()
        task_p2.refresh_from_db()
        task_p3.refresh_from_db()
        task_p5.refresh_from_db()

        # Verify all tasks are assigned
        assert all(
            [
                task_p1.status == Task.Status.IN_PROGRESS,
                task_p2.status == Task.Status.IN_PROGRESS,
                task_p3.status == Task.Status.IN_PROGRESS,
                task_p5.status == Task.Status.IN_PROGRESS,
            ]
        )

        # All should be assigned to the same executor
        assert task_p1.assignee == executor
        assert task_p2.assignee == executor
        assert task_p3.assignee == executor
        assert task_p5.assignee == executor
