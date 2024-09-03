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

    @action(detail=True)
    def task_assign(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.validate_profile is None:
            instance.validate_profile = request.user.profile
            instance.save()
            return Response(PendingTaskSerializer(instance).data)
        else:
            return Response({'error': 'Unable to assign task'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def task_unassign(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.validate_profile == request.user.profile:
            if instance.status == 0:
                instance.validate_profile = None
                instance.save()
                return Response(PendingTaskSerializer(instance).data)
            else:
                return Response({'error': 'Task is in process or finished'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Unable to unassign task'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def updated_task_status(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.validate_profile == request.user.profile:
            new_status = request.data.get('status')
            if new_status in [0, 1, 2]:
                instance.status = new_status
                instance.save()
                return Response(PendingTaskSerializer(instance).data)
            else:
                return Response({'error': 'Invalid status'},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Unable to update task'},
                        status=status.HTTP_400_BAD_REQUEST)
