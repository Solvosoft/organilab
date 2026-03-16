from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pending_tasks import views
from pending_tasks.api.views import PendingTaskViewSet

router = DefaultRouter()
router.register("pending-tasks", PendingTaskViewSet, basename="pending_tasks")

app_name = "pending_tasks"

urlpatterns = [
    path("api/", include(router.urls)),
    path("view-task", views.view_task, name="view_task"),
]
