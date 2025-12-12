from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from core.models import Executor, Task
from core.serializers import (
    ExecutorSerializer,
    ExecutorUpdateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)
from core.selectors import get_global_stats, get_executor_stats


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Task resources.

    Provides CRUD operations for tasks.
    - List: GET /tasks/
    - Create: POST /tasks/
    - Retrieve: GET /tasks/{uuid}/
    - Update: PUT /tasks/{uuid}/
    - Partial Update: PATCH /tasks/{uuid}/
    - Delete: DELETE /tasks/{uuid}/
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ["update", "partial_update"]:
            return TaskUpdateSerializer
        return TaskSerializer


class ExecutorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Executor resources.

    Provides CRUD operations for executors.
    - List: GET /executors/
    - Create: POST /executors/
    - Retrieve: GET /executors/{id}/
    - Update: PUT /executors/{id}/
    - Partial Update: PATCH /executors/{id}/
    - Delete: DELETE /executors/{id}/
    """

    queryset = Executor.objects.all()
    serializer_class = ExecutorSerializer

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ["update", "partial_update"]:
            return ExecutorUpdateSerializer
        return ExecutorSerializer


class StatsViewSet(viewsets.ViewSet):
    """
    ViewSet for retrieving system statistics.

    Provides read-only endpoints for system and executor stats.
    """

    @extend_schema(
        responses={200: dict},
        description="Get global task statistics grouped by status",
    )
    @action(detail=False, methods=["get"], url_path="global")
    def global_stats(self, request):
        """
        Get global statistics of tasks grouped by status.

        Returns:
            - pending: Number of pending tasks
            - in_progress: Number of in-progress tasks
            - completed: Number of completed tasks
            - total: Total number of tasks
        """
        stats = get_global_stats()
        return Response(stats, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: list},
        description="Get statistics for all executors with their current task load",
    )
    @action(detail=False, methods=["get"], url_path="executors")
    def executor_stats(self, request):
        """
        Get statistics for all executors with their current task load.

        Returns list of executor information including:
            - id, name, max_tasks
            - active_tasks, pending_tasks, in_progress_tasks, completed_tasks
        """
        stats = get_executor_stats()
        return Response(stats, status=status.HTTP_200_OK)
