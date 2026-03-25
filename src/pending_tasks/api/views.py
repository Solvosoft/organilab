import logging

from django.contrib.admin.models import CHANGE, ADDITION
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pending_tasks.api.model_viewset_without_create import (
    AuthAllPermBaseObjectWithoutCreate,
)
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from auth_and_perms.models import Profile
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from pending_tasks.api import filterset
from pending_tasks.models import PendingTask
from report.utils import create_notification
from pending_tasks.api.serializers import (
    PendingTaskSerializer,
    PendingTaskListSerializer,
    PendingTaskValidateSerializer,
    ProfileValidateSerializer,
    CurrentStatusValidateSerializer,
    NewStatusValidateSerializer,
    PendingTaskGetValuesSerializer,
)

logger = logging.getLogger("organilab")


class PendingTaskViewSet(mixins.CreateModelMixin, AuthAllPermBaseObjectWithoutCreate):
    serializer_class = {
        "list": PendingTaskListSerializer,
        "create": PendingTaskValidateSerializer,
        "destroy": PendingTaskSerializer,
        "update": PendingTaskValidateSerializer,
        "partial_update": PendingTaskValidateSerializer,
        "retrieve": PendingTaskGetValuesSerializer,
        "get_values_for_update": PendingTaskGetValuesSerializer,
    }

    perms = {
        "list": ["pending_tasks.view_pendingtask"],
        "create": ["pending_tasks.add_pendingtask"],
        "retrieve": ["pending_tasks.view_pendingtask"],
        "get_values_for_update": ["pending_tasks.view_pendingtask"],
        "update": ["pending_tasks.change_pendingtask"],
        "partial_update": ["pending_tasks.change_pendingtask"],
        "destroy": ["pending_tasks.delete_pendingtask"],
        "task_assign": ["pending_tasks.change_pendingtask"],
        "task_unassign": ["pending_tasks.change_pendingtask"],
        "updated_task_status": ["pending_tasks.change_pendingtask"],
        "archive_finished": ["pending_tasks.change_pendingtask"],
    }

    queryset = PendingTask.objects.all()
    search_fields = ["description"]
    filterset_class = filterset.PendingTaskFilterSet
    ordering_fields = ["creation_date"]
    ordering = ("-creation_date",)

    def perform_create(self, serializer):
        org = get_object_or_404(OrganizationStructure, pk=self.kwargs.get("org_pk"))
        instance = serializer.save(organization=org, created_by=self.request.user)
        organilab_logentry(
            self.request.user,
            instance,
            ADDITION,
            changed_data=["name", "description", "status"],
        )
        self.notify_task_created(instance, org)

    def notify_task_created(self, instance, org):
        url = reverse("pending_tasks:view_task", kwargs={"org_pk": org.pk})
        message = _("New pending task: %s") % instance.name

        users_to_notify = set()

        if instance.profile_id and instance.profile.user_id:
            users_to_notify.add(instance.profile.user_id)

        role_user_ids = Profile.objects.filter(
            profilepermission__rol__in=instance.rols.all()
        ).values_list("user_id", flat=True)
        users_to_notify.update(role_user_ids)

        users_to_notify.discard(self.request.user.pk)

        User = get_user_model()
        for user in User.objects.filter(pk__in=users_to_notify):
            create_notification(user, message, url)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        profile = self.request.user.profile
        rols = profile.profilepermission_set.all().values_list("rol", flat=True)
        org_pk = self.kwargs.get("org_pk")
        queryset = (
            queryset.filter(organization_id=org_pk)
            .filter(
                Q(profile=profile) | Q(rols__in=rols) | Q(created_by=self.request.user)
            )
            .filter(is_archived=False)
            .distinct()
        )
        return queryset

    def _get_task_and_data(self, request):
        task = self.get_object()
        data = {"profile": request.user.profile.id}
        data.update(request.data)
        return task, data

    def _execute_task_action(self, request, serializer_class, apply_changes):
        task, data = self._get_task_and_data(request)
        serializer = serializer_class(data=data, context={"task": task})
        if serializer.is_valid():
            changed_data = apply_changes(task, serializer)
            task.save()
            organilab_logentry(request.user, task, CHANGE, changed_data=changed_data)
            return Response(PendingTaskSerializer(task).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def task_assign(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.profile = serializer.validated_data["profile"]
            return ["profile"]

        return self._execute_task_action(
            request, ProfileValidateSerializer, apply_changes
        )

    @action(detail=True)
    def task_unassign(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.profile = None
            return ["profile"]

        return self._execute_task_action(
            request, CurrentStatusValidateSerializer, apply_changes
        )

    @action(detail=True, methods=["patch"])
    def updated_task_status(self, request, *args, **kwargs):
        def apply_changes(task, serializer):
            task.status = serializer.validated_data.get("status")
            return ["status"]

        return self._execute_task_action(
            request, NewStatusValidateSerializer, apply_changes
        )

    @action(detail=False, methods=["post"], url_path="archive_finished")
    def archive_finished(self, request, *args, **kwargs):
        org = get_object_or_404(OrganizationStructure, pk=self.kwargs.get("org_pk"))
        profile = request.user.profile
        rols = profile.profilepermission_set.all().values_list("rol", flat=True)
        updated = (
            PendingTask.objects.filter(
                organization=org,
                status=PendingTask.FINISHED,
                is_archived=False,
            )
            .filter(Q(profile=profile) | Q(rols__in=rols) | Q(created_by=request.user))
            .distinct()
            .update(is_archived=True)
        )
        return Response({"archived": updated}, status=status.HTTP_200_OK)
