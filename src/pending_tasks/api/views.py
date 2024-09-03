from django.db.models import Q
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

from pending_tasks.models import PendingTask
from pending_tasks.api.serializers import PendingTaskSerializer, \
    PendingTaskListSerializer, PendingTaskValidateSerializer


class PendingTaskViewSet(AuthAllPermBaseObjectManagement):
    queryset = PendingTask.objects.all()

    serializer_class = {
        'list': PendingTaskListSerializer,
        'destroy': PendingTaskSerializer,
        'create': PendingTaskValidateSerializer,
        'update': PendingTaskValidateSerializer,
    }

    permission_classes = (BasePermission,)

    ordering = ('creation_date',)

    def get_queryset(self):
        return PendingTask.objects.filter(
            Q(validate_profile=self.request.user.profile) | Q(
                validate_profile__isnull=True))
