from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from presentation.models import SystemParameter
from presentation.parameters import (
    DATA_TYPES,
    ORIGIN_OWN,
    ORIGINS,
    cast_value,
    get_definition,
    resolve_parameter,
    serialize_value,
    visible_parameters,
)
from presentation.platform.base import ADDITION, CHANGE, DELETION, RegistryViewSet


class ParameterValueSerializer(serializers.Serializer):
    value = serializers.CharField(allow_blank=True, required=False, default="")


class SystemParameterViewSet(RegistryViewSet):
    perms = {
        "list": ["presentation.view_systemparameter"],
        "retrieve": ["presentation.view_systemparameter"],
        "get_values_for_update": ["presentation.change_systemparameter"],
        "update": ["presentation.change_systemparameter"],
        "restore": ["presentation.change_systemparameter"],
    }

    def row(self, key):
        definition = get_definition(key)
        resolved = resolve_parameter(self.get_organization(), key)
        can_change = self.request.user.has_perm("presentation.change_systemparameter")
        return {
            "id": key,
            "key": key,
            "label": str(definition["label"]),
            "description": str(definition.get("description", "")),
            "data_type": str(dict(DATA_TYPES)[definition["type"]]),
            "value": serialize_value(definition["type"], resolved["value"]),
            "origin": resolved["origin"],
            "origin_display": "%s%s" % (
                ORIGINS[resolved["origin"]],
                " (%s)" % resolved["source"] if resolved["source"] and resolved["origin"] != ORIGIN_OWN else "",
            ),
            "actions": {
                "update": can_change,
                "restore": can_change and resolved["origin"] == ORIGIN_OWN,
                "destroy": False,
            },
        }

    def get_key(self, pk):
        if pk not in visible_parameters(self.request.user):
            raise Http404
        return pk

    def list(self, request, org_pk=None):
        return Response(self.datatable([self.row(key) for key in visible_parameters(request.user)]))

    def retrieve(self, request, org_pk=None, pk=None):
        return Response(self.row(self.get_key(pk)))

    @action(detail=True, methods=["get"])
    def get_values_for_update(self, request, org_pk=None, pk=None):
        return Response(self.row(self.get_key(pk)))

    def update(self, request, org_pk=None, pk=None):
        key = self.get_key(pk)
        serializer = ParameterValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_type = get_definition(key)["type"]
        try:
            value = cast_value(data_type, serializer.validated_data["value"])
        except (TypeError, ValueError):
            raise serializers.ValidationError({"value": [_("Invalid value for this parameter.")]})
        parameter, created = SystemParameter.objects.update_or_create(
            organization=self.get_organization(),
            key=key,
            defaults={"raw_value": serialize_value(data_type, value)},
        )
        if created:
            parameter.created_by = request.user
            parameter.save(update_fields=["created_by"])
        self.log(parameter, ADDITION if created else CHANGE, _("Updated"), ["raw_value"])
        return Response(self.row(key))

    @action(detail=True, methods=["post"])
    def restore(self, request, org_pk=None, pk=None):
        key = self.get_key(pk)
        parameter = SystemParameter.objects.filter(organization=self.get_organization(), key=key).first()
        if parameter is not None:
            self.log(parameter, DELETION, _("Restored inherited value"))
            parameter.delete()
        return Response({"detail": _("The inherited value was restored.")})
