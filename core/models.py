import uuid
from django.db import models


class Executor(models.Model):
    """Represents an executor who can be assigned tasks."""

    name = models.CharField(max_length=255, unique=True)
    max_tasks = models.IntegerField()

    class Meta:
        db_table = "executors"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    """Represents a task that can be assigned to an executor."""

    class Priority(models.IntegerChoices):
        LOWEST = 1, "Lowest"
        LOW = 2, "Low"
        MEDIUM = 3, "Medium"
        HIGH = 4, "High"
        HIGHEST = 5, "Highest"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    assignee = models.ForeignKey(
        Executor, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self):
        return f"Task {self.uuid} - {self.status}"
