from django.urls import path, include
from rest_framework.routers import DefaultRouter

from pending_tasks.api.views import PendingTaskViewSet

router = DefaultRouter()
router.register('api_pending_tasks', PendingTaskViewSet, basename='pending_tasks')

app_name = 'pending_tasks'

urlpatterns = [
    path('api/', include(router.urls)),
]
