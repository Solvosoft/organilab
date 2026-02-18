import logging

from django.contrib.admin.models import ADDITION, CHANGE
from django.db.models import Q

from pending_tasks.api.model_viewset_without_create import AuthAllPermBaseObjectWithoutCreate
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
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
        'create_task': PendingTaskValidateSerializer,
    }

    perms = {
        'list': ["pending_tasks.view_pending_task"],
        'update': ["pending_tasks.change_pending_task"],
        'destroy': ["pending_tasks.delete_pending_task"],
        'create_task': ["pending_tasks.add_pending_task"],
    }

    permission_classes = (BasePermission,)

    queryset = PendingTask.objects.all()
    search_fields = ['description']
    filterset_class = filterset.PendingTaskFilterSet
    ordering_fields = ['creation_date']
    ordering = ('-creation_date',)

    def filter_queryset(self, queryset):
        if not self.request.user.is_authenticated:
            return queryset.none()
        profile = self.request.user.profile
        rols = profile.profilepermission_set.all().values_list('rol', flat=True)
        queryset = queryset.filter(
            Q(profile=profile) | Q(profile__isnull=True, rols__in=rols)
        )
        return super().filter_queryset(queryset)

    def _get_task_and_data(self, request):
        task = self.get_object()
        data = {'profile': request.user.profile.id}
        data.update(request.data)
        return task, data

    @action(detail=True)
    def task_assign(self, request, *args, **kwargs):
        task, data = self._get_task_and_data(request)
        serializer = ProfileValidateSerializer(data=data, context={'task': task})
        if serializer.is_valid():
            task.profile = serializer.validated_data['profile']
            task.save()
            organilab_logentry(request.user, task, CHANGE, "pending task", changed_data=['profile'])
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def task_unassign(self, request, *args, **kwargs):
        task, data = self._get_task_and_data(request)
        serializer = CurrentStatusValidateSerializer(data=data, context={'task': task})
        if serializer.is_valid():
            task.profile = None
            task.save()
            organilab_logentry(request.user, task, CHANGE, "pending task", changed_data=['profile'])
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def updated_task_status(self, request, *args, **kwargs):
        task, data = self._get_task_and_data(request)
        serializer = NewStatusValidateSerializer(data=data, context={'task': task})
        if serializer.is_valid():
            task.status = serializer.validated_data.get('status')
            task.save()
            organilab_logentry(request.user, task, CHANGE, "pending task", changed_data=['status'])
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_task(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'profile' not in data or not data['profile']:
            data['profile'] = request.user.profile.pk
        if 'rols' not in data:
            data['rols'] = []
        serializer = PendingTaskValidateSerializer(data=data)
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)
            organilab_logentry(
                request.user, task, ADDITION, "pending task",
                changed_data=['description', 'status', 'profile', 'link']
            )
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
