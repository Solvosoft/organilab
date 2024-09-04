import logging

from django.db.models import Q
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

from pending_tasks.models import PendingTask
from pending_tasks.api.serializers import PendingTaskSerializer, \
    PendingTaskListSerializer, PendingTaskValidateSerializer

logger = logging.getLogger("django")


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
            logger.info(f"Task {instance.id} assigned to user {request.user.username}")
            return Response(PendingTaskSerializer(instance).data)
        else:
            logger.warning(
                f"Task {instance.id} could not be assigned, already assigned to {instance.validate_profile.user.username}")
            return Response({'error': 'Unable to assign task'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def task_unassign(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.validate_profile == request.user.profile:
            if instance.status == 0:
                instance.validate_profile = None
                instance.save()
                logger.info(
                    f"Task {instance.id} unassigned from user {request.user.username}")
                return Response(PendingTaskSerializer(instance).data)
            else:
                logger.warning(
                    f"Task {instance.id} could not be unassigned, status is {instance.status}")
                return Response({'error': 'Task is in process or finished'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(
                f"User {request.user.username} tried to unassign task {instance.id}, but is not assigned")
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
                logger.info(
                    f"Task {instance.id} status updated to {new_status} by user {request.user.username}")
                return Response(PendingTaskSerializer(instance).data)
            else:
                logger.warning(
                    f"Invalid status {new_status} provided for task {instance.id}")
                return Response({'error': 'Invalid status'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(
                f"User {request.user.username} tried to update task {instance.id}, but is not assigned")
            return Response({'error': 'Unable to update task'},
                            status=status.HTTP_400_BAD_REQUEST)
