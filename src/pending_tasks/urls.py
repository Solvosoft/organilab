from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pending_tasks import views
from pending_tasks.api.views import PendingTaskViewSet

router_pending_tasks = DefaultRouter()
router_pending_tasks.register(
    "api_pending_tasks", PendingTaskViewSet, basename="api-pending_tasks"
)

app_name = "pending_tasks"

urlpatterns = [
    path("api/", include(router_pending_tasks.urls)),
    path("view-tasks", views.view_task, name="view_task"),
]
