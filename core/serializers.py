from rest_framework import serializers

from core.models import Executor, Task


class ExecutorSerializer(serializers.ModelSerializer):
    """Serializer for Executor model with all standard fields."""

    class Meta:
        model = Executor
        fields = ["id", "name", "max_tasks"]
        read_only_fields = ["id"]


class ExecutorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Executor, only allows max_tasks updates."""

    class Meta:
        model = Executor
        fields = ["max_tasks"]


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with read-only fields for assignee and dates."""

    assignee = ExecutorSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "uuid",
            "description",
            "priority",
            "status",
            "assignee",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["uuid", "assignee", "created_at", "completed_at"]


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Task, only allows status updates."""

    class Meta:
        model = Task
        fields = ["status"]
