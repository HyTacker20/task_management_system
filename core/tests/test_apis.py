import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Executor, Task


@pytest.fixture
def api_client(db):
    """Create an authenticated API client for testing."""
    client = APIClient()
    user = User.objects.create_user(username="tester", password="pass1234")
    client.force_authenticate(user=user)
    return client


@pytest.mark.integration
class TestTasksAPI:
    """Integration tests for Tasks API endpoints."""

    def test_create_task_success(self, db, api_client):
        """Verify creating a task works."""
        url = reverse("task-list")
        data = {
            "description": "New task from API",
            "priority": Task.Priority.HIGH,
            "status": Task.Status.PENDING,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["description"] == data["description"]
        assert response.data["priority"] == data["priority"]
        assert response.data["status"] == data["status"]
        assert "uuid" in response.data
        assert response.data["assignee"] is None
        assert "created_at" in response.data
        assert response.data["completed_at"] is None

        # Verify task created in database
        task = Task.objects.get(uuid=response.data["uuid"])
        assert task.description == data["description"]
        assert task.priority == data["priority"]

    def test_create_task_with_minimal_data(self, db, api_client):
        """Verify creating a task with only description works (defaults applied)."""
        url = reverse("task-list")
        data = {"description": "Minimal task"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["description"] == data["description"]
        assert response.data["priority"] == Task.Priority.MEDIUM  # Default
        assert response.data["status"] == Task.Status.PENDING  # Default

    def test_list_tasks(self, db, api_client, multiple_tasks):
        """Verify listing tasks works."""
        url = reverse("task-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get("results", [])) == len(multiple_tasks)

    def test_retrieve_task(self, db, api_client, sample_task):
        """Verify retrieving a single task works."""
        url = reverse("task-detail", kwargs={"pk": sample_task.uuid})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["uuid"] == str(sample_task.uuid)
        assert response.data["description"] == sample_task.description

    def test_update_task_status_success(self, db, api_client, sample_task):
        """Verify updating a task's status works."""
        url = reverse("task-detail", kwargs={"pk": sample_task.uuid})
        data = {"status": Task.Status.COMPLETED}

        # Initial state
        assert sample_task.status == Task.Status.PENDING

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == Task.Status.COMPLETED

        # Verify database updated
        sample_task.refresh_from_db()
        assert sample_task.status == Task.Status.COMPLETED

    def test_update_task_restricted_fields_ignored(
        self, db, api_client, sample_task_with_executor
    ):
        """Verify that trying to update restricted fields (priority, assignee) is ignored."""
        url = reverse("task-detail", kwargs={"pk": sample_task_with_executor.uuid})

        # Store original values
        original_priority = sample_task_with_executor.priority
        original_assignee = sample_task_with_executor.assignee
        original_description = sample_task_with_executor.description

        # Attempt to update restricted fields
        data = {
            "status": Task.Status.COMPLETED,
            "priority": Task.Priority.LOWEST,  # Should be ignored
            "assignee": None,  # Should be ignored
            "description": "Changed description",  # Should be ignored
        }

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify only status changed
        sample_task_with_executor.refresh_from_db()
        assert sample_task_with_executor.status == Task.Status.COMPLETED
        assert sample_task_with_executor.priority == original_priority
        assert sample_task_with_executor.assignee == original_assignee
        assert sample_task_with_executor.description == original_description

    def test_delete_task(self, db, api_client, sample_task):
        """Verify deleting a task works."""
        url = reverse("task-detail", kwargs={"pk": sample_task.uuid})
        task_uuid = sample_task.uuid

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify task deleted from database
        assert not Task.objects.filter(uuid=task_uuid).exists()


@pytest.mark.integration
class TestExecutorsAPI:
    """Integration tests for Executors API endpoints."""

    def test_create_executor_success(self, db, api_client):
        """Verify creating an executor works."""
        url = reverse("executor-list")
        data = {"name": "Test-Executor-API", "max_tasks": 8}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["max_tasks"] == data["max_tasks"]
        assert "id" in response.data

        # Verify executor created in database
        executor = Executor.objects.get(id=response.data["id"])
        assert executor.name == data["name"]
        assert executor.max_tasks == data["max_tasks"]

    def test_list_executors(self, db, api_client, multiple_executors):
        """Verify listing executors works."""
        url = reverse("executor-list")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get("results", [])) == len(multiple_executors)

    def test_retrieve_executor(self, db, api_client, sample_executor):
        """Verify retrieving a single executor works."""
        url = reverse("executor-detail", kwargs={"pk": sample_executor.id})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_executor.id
        assert response.data["name"] == sample_executor.name

    def test_update_executor_max_tasks_success(self, db, api_client, sample_executor):
        """Verify updating an executor's max_tasks works."""
        url = reverse("executor-detail", kwargs={"pk": sample_executor.id})
        data = {"max_tasks": 10}

        # Initial state
        assert sample_executor.max_tasks == 5

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["max_tasks"] == 10

        # Verify database updated
        sample_executor.refresh_from_db()
        assert sample_executor.max_tasks == 10

    def test_update_executor_name_ignored(self, db, api_client, sample_executor):
        """Verify that trying to update executor name is ignored."""
        url = reverse("executor-detail", kwargs={"pk": sample_executor.id})

        original_name = sample_executor.name

        # Attempt to update name (should be ignored)
        data = {"max_tasks": 8, "name": "Changed-Name"}  # Should be ignored

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["max_tasks"] == 8

        # Verify name unchanged
        sample_executor.refresh_from_db()
        assert sample_executor.name == original_name
        assert sample_executor.max_tasks == 8

    def test_delete_executor(self, db, api_client, sample_executor):
        """Verify deleting an executor works."""
        url = reverse("executor-detail", kwargs={"pk": sample_executor.id})
        executor_id = sample_executor.id

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify executor deleted from database
        assert not Executor.objects.filter(id=executor_id).exists()


@pytest.mark.integration
class TestStatsAPI:
    """Integration tests for Statistics API endpoints."""

    def test_global_stats_endpoint_returns_correct_structure(
        self, db, api_client, multiple_tasks
    ):
        """Verify the /stats/global/ endpoint returns 200 OK and correct structure."""
        url = reverse("stats-global-stats")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify correct structure
        assert "pending" in response.data
        assert "in_progress" in response.data
        assert "completed" in response.data
        assert "total" in response.data

        # Verify data types
        assert isinstance(response.data["pending"], int)
        assert isinstance(response.data["in_progress"], int)
        assert isinstance(response.data["completed"], int)
        assert isinstance(response.data["total"], int)

        # Verify total equals sum of statuses
        assert response.data["total"] == (
            response.data["pending"]
            + response.data["in_progress"]
            + response.data["completed"]
        )

    def test_global_stats_with_known_data(self, db, api_client):
        """Verify global stats returns correct counts for known data."""
        # Create tasks with known statuses
        Task.objects.create(
            description="Task 1", priority=1, status=Task.Status.PENDING
        )
        Task.objects.create(
            description="Task 2", priority=1, status=Task.Status.PENDING
        )
        Task.objects.create(
            description="Task 3", priority=1, status=Task.Status.IN_PROGRESS
        )
        Task.objects.create(
            description="Task 4", priority=1, status=Task.Status.COMPLETED
        )

        url = reverse("stats-global-stats")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["pending"] == 2
        assert response.data["in_progress"] == 1
        assert response.data["completed"] == 1
        assert response.data["total"] == 4

    def test_executor_stats_endpoint_returns_correct_structure(
        self, db, api_client, multiple_executors, multiple_tasks
    ):
        """Verify the /stats/executors/ endpoint returns 200 OK and correct structure."""
        url = reverse("stats-executor-stats")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify response is a list
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verify structure of first executor
        executor_data = response.data[0]
        assert "id" in executor_data
        assert "name" in executor_data
        assert "max_tasks" in executor_data
        assert "active_tasks" in executor_data
        assert "pending_tasks" in executor_data
        assert "in_progress_tasks" in executor_data
        assert "completed_tasks" in executor_data

        # Verify data types
        assert isinstance(executor_data["id"], int)
        assert isinstance(executor_data["name"], str)
        assert isinstance(executor_data["max_tasks"], int)
        assert isinstance(executor_data["active_tasks"], int)
        assert isinstance(executor_data["pending_tasks"], int)
        assert isinstance(executor_data["in_progress_tasks"], int)
        assert isinstance(executor_data["completed_tasks"], int)

    def test_executor_stats_with_known_data(self, db, api_client):
        """Verify executor stats returns correct counts for known data."""
        # Create executor
        executor = Executor.objects.create(name="Test-Executor", max_tasks=10)

        # Create tasks with different statuses
        Task.objects.create(
            description="Pending task",
            priority=1,
            status=Task.Status.PENDING,
            assignee=executor,
        )
        Task.objects.create(
            description="In progress task",
            priority=1,
            status=Task.Status.IN_PROGRESS,
            assignee=executor,
        )
        Task.objects.create(
            description="Completed task",
            priority=1,
            status=Task.Status.COMPLETED,
            assignee=executor,
        )

        url = reverse("stats-executor-stats")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        executor_data = response.data[0]
        assert executor_data["id"] == executor.id
        assert executor_data["name"] == "Test-Executor"
        assert executor_data["max_tasks"] == 10
        assert executor_data["pending_tasks"] == 1
        assert executor_data["in_progress_tasks"] == 1
        assert executor_data["completed_tasks"] == 1
        assert executor_data["active_tasks"] == 2  # pending + in_progress

    def test_stats_endpoints_with_empty_database(self, db, api_client):
        """Verify stats endpoints work correctly with empty database."""
        # Test global stats
        global_url = reverse("stats-global-stats")
        global_response = api_client.get(global_url)

        assert global_response.status_code == status.HTTP_200_OK
        assert global_response.data["pending"] == 0
        assert global_response.data["in_progress"] == 0
        assert global_response.data["completed"] == 0
        assert global_response.data["total"] == 0

        # Test executor stats
        executor_url = reverse("stats-executor-stats")
        executor_response = api_client.get(executor_url)

        assert executor_response.status_code == status.HTTP_200_OK
        assert isinstance(executor_response.data, list)
        assert len(executor_response.data) == 0
