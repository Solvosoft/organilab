import logging

from django.contrib.admin.models import CHANGE, ADDITION
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.permission_management import AllPermissionByAction
from rest_framework import mixins, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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
    PendingTaskGetValuesSerializer,
)

logger = logging.getLogger("organilab")


class PendingTaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (AllPermissionByAction,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)

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
        "archive_finished": ["pending_tasks.change_pendingtask"],
    }

    queryset = PendingTask.objects.all()
    search_fields = ["description"]
    filterset_class = filterset.PendingTaskFilterSet
    ordering_fields = ["creation_date"]
    ordering = ("-creation_date",)

    def get_serializer_class(self):
        if self.action in self.serializer_class:
            return self.serializer_class[self.action]
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": self.queryset.count(),
            "recordsFiltered": queryset.count(),
            "draw": request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)

    @action(detail=True, methods=["get"])
    def get_values_for_update(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(self.get_serializer(instance).data)

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
        return (
            queryset.filter(
                Q(profile=profile) | Q(rols__in=rols) | Q(created_by=self.request.user)
            )
            .filter(is_archived=False)
            .distinct()
        )

    @action(detail=False, methods=["post"], url_path="archive_finished")
    def archive_finished(self, request, *args, **kwargs):
        profile = request.user.profile
        rols = profile.profilepermission_set.all().values_list("rol", flat=True)
        updated = (
            PendingTask.objects.filter(status=PendingTask.FINISHED, is_archived=False)
            .filter(Q(profile=profile) | Q(rols__in=rols) | Q(created_by=request.user))
            .distinct()
            .update(is_archived=True)
        )
        return Response({"archived": updated}, status=status.HTTP_200_OK)