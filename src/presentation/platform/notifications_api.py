from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from presentation.models import NotificationSetting
from presentation.notifications import registered_processes, resolve_setting
from presentation.platform.base import ADDITION, CHANGE, DELETION, RegistryViewSet


class NotificationSettingSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False, default=True)
    override_subject = serializers.CharField(required=False, allow_blank=True, default="", max_length=500)
    override_message = serializers.CharField(required=False, allow_blank=True, default="")


class NotificationSettingViewSet(RegistryViewSet):
    perms = {
        "list": ["presentation.view_notificationsetting"],
        "retrieve": ["presentation.view_notificationsetting"],
        "get_values_for_update": ["presentation.change_notificationsetting"],
        "update": ["presentation.change_notificationsetting"],
        "restore": ["presentation.change_notificationsetting"],
    }

    def row(self, code, config):
        organization = self.get_organization()
        setting, origin = resolve_setting(organization, code)
        own = setting is not None and origin == organization
        can_change = self.request.user.has_perm("presentation.change_notificationsetting")
        if setting is None:
            origin_display = _("Default")
        elif own:
            origin_display = _("Own")
        else:
            origin_display = "%s (%s)" % (_("Inherited"), origin)
        return {
            "id": code,
            "code": code,
            "default_subject": config.get("subject", ""),
            "is_active": setting.is_active if setting else True,
            "override_subject": setting.override_subject if setting else "",
            "override_message": setting.override_message if setting else "",
            "origin_display": str(origin_display),
            "actions": {"update": can_change, "restore": can_change and own, "destroy": False},
        }

    def get_config(self, pk):
        config = registered_processes().get(pk)
        if config is None:
            raise Http404
        return config

    def list(self, request, org_pk=None):
        return Response(self.datatable([self.row(code, config) for code, config in registered_processes().items()]))

    def retrieve(self, request, org_pk=None, pk=None):
        return Response(self.row(pk, self.get_config(pk)))

    @action(detail=True, methods=["get"])
    def get_values_for_update(self, request, org_pk=None, pk=None):
        return Response(self.row(pk, self.get_config(pk)))

    def update(self, request, org_pk=None, pk=None):
        config = self.get_config(pk)
        serializer = NotificationSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        setting, created = NotificationSetting.objects.update_or_create(
            organization=self.get_organization(), code=pk, defaults=serializer.validated_data
        )
        if created:
            setting.created_by = request.user
            setting.save(update_fields=["created_by"])
        self.log(setting, ADDITION if created else CHANGE, _("Updated"), list(serializer.validated_data))
        return Response(self.row(pk, config))

    @action(detail=True, methods=["post"])
    def restore(self, request, org_pk=None, pk=None):
        self.get_config(pk)
        setting = NotificationSetting.objects.filter(organization=self.get_organization(), code=pk).first()
        if setting is not None:
            self.log(setting, DELETION, _("Restored inherited value"))
            setting.delete()
        return Response({"detail": _("The inherited value was restored.")})
