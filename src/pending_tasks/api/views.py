import logging

from django.contrib.admin.models import CHANGE
from django.db.models import Q

from pending_tasks.api.model_viewset_without_create import AuthAllPermBaseObjectWithoutCreate
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from laboratory.utils import organilab_logentry
from pending_tasks.api import filterset
from pending_tasks.models import PendingTask
from pending_tasks.api.serializers import PendingTaskSerializer, \
    PendingTaskListSerializer, PendingTaskValidateSerializer, ProfileValidateSerializer, \
    CurrentStatusValidateSerializer, NewStatusValidateSerializer

logger = logging.getLogger("organilab")


class PendingTaskViewSet(AuthAllPermBaseObjectWithoutCreate):
    serializer_class = {
        'list': PendingTaskListSerializer,
        'destroy': PendingTaskSerializer,
        'update': PendingTaskValidateSerializer,
    }

    perms = {
        'list': ["pending_tasks.view_pendingtask"],
        'update': ["pending_tasks.change_pendingtask"],
        'destroy': ["pending_tasks.delete_pendingtask"],
        'task_assign': ["pending_tasks.change_pendingtask"],
        'task_unassign': ["pending_tasks.change_pendingtask"],
        'updated_task_status': ["pending_tasks.change_pendingtask"],
    }

    queryset = PendingTask.objects.all()
    search_fields = ['description']
    filterset_class = filterset.PendingTaskFilterSet
    ordering_fields = ['creation_date']
    ordering = ('-creation_date',)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        profile = self.request.user.profile
        rols = profile.profilepermission_set.all().values_list('rol', flat=True)
        queryset = queryset.filter(
            Q(profile=profile) |
            Q(profile__isnull=True, rols__in=rols)
        ).distinct()
        return queryset

    def _get_task_and_data(self, request):
        task = self.get_object()
        data = {'profile': request.user.profile.id}
        data.update(request.data)
        return task, data

    def _execute_task_action(self, request, serializer_class, apply_changes):
        task, data = self._get_task_and_data(request)
        serializer = serializer_class(data=data, context={'task': task})
        if serializer.is_valid():
            changed_data = apply_changes(task, serializer)
            task.save()
            organilab_logentry(request.user, task, CHANGE, changed_data=changed_data)
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def task_assign(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.profile = serializer.validated_data['profile']
            return ['profile']
        return self._execute_task_action(request, ProfileValidateSerializer, apply_changes)

    @action(detail=True)
    def task_unassign(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.profile = None
            return ['profile']
        return self._execute_task_action(request, CurrentStatusValidateSerializer, apply_changes)

    @action(detail=True, methods=['patch'])
    def updated_task_status(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.status = serializer.validated_data.get('status')
            return ['status']
        return self._execute_task_action(request, NewStatusValidateSerializer, apply_changes)
