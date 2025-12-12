from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.apis.views import ExecutorViewSet, StatsViewSet, TaskViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"executors", ExecutorViewSet, basename="executor")
router.register(r"stats", StatsViewSet, basename="stats")

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
]
