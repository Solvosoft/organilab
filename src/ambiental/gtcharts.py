"""Gráficos del panel ambiental (``djgentelella.chartjs``).

``register_lookups`` no devuelve la clase decorada, así que la lógica común vive en
``AmbientalBaseChart``, sin decorar, y cada gráfico hereda de ella.
"""
import datetime
from collections import OrderedDict
from random import randint

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from djgentelella.chartjs import HorizontalBarChart, LineChart, StackedBarChart
from djgentelella.groute import register_lookups
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from ambiental.ambiental_defaults import (
    KEY_NORMALIZER,
    KEY_RESOURCE_TYPE,
    NORMALIZER_PERSON,
    RESOURCE_WATER,
)
from ambiental.indicators import compute_indicator
from ambiental.models import ConsumptionRecord
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import Catalog, OrganizationStructure
from risk_management.gtcharts import BaseChart, LaboratoryPermission
from risk_management.models import Buildings

MONTHS = (
    _("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"),
    _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec"),
)


class ChartFilterSerializer(serializers.Serializer):
    year = serializers.IntegerField(required=False, min_value=1900, max_value=2200)
    building = serializers.IntegerField(required=False)
    resource_type = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key=KEY_RESOURCE_TYPE), required=False
    )
    normalizer = serializers.PrimaryKeyRelatedField(
        queryset=Catalog.objects.filter(key=KEY_NORMALIZER), required=False
    )


class AmbientalBaseChart(BaseChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["ambiental.view_ambiental_dashboard"]

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        user_is_allowed_on_organization(request.user, self.organization)
        self.load_filters()
        return Response(self.serializer_class(self.get_graph_data()).data)

    def load_filters(self):
        serializer = ChartFilterSerializer(data=self.request.query_params)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        data = serializer.validated_data
        self.year = data.get("year") or datetime.date.today().year
        self.building = None
        if data.get("building"):
            self.building = get_object_or_404(
                Buildings, pk=data["building"], organization=self.organization
            )
        self.resource_type = data.get("resource_type")
        self.normalizer = data.get("normalizer")

    def records(self):
        queryset = ConsumptionRecord.objects.filter(
            organization=self.organization, period_end__year=self.year
        )
        if self.building is not None:
            queryset = queryset.filter(point__building=self.building)
        if self.resource_type is not None:
            queryset = queryset.filter(point__resource_type=self.resource_type)
        return queryset

    def dataset(self, label, data, fill=False):
        if not hasattr(self, "index"):
            self.index = randint(0, len(self.colors) - 1)
        color = self.get_color()
        return {
            "label": str(label),
            "backgroundColor": color,
            "borderColor": color,
            "borderWidth": 1,
            "fill": fill,
            "data": data,
        }

    def monthly_series(self, value_field, series_fields):
        """``{serie: [12 valores]}`` sumando ``value_field`` por mes de ``period_end``."""
        series = OrderedDict()
        rows = self.records().order_by(*series_fields).values_list(
            *series_fields, "period_end", value_field
        )
        for row in rows:
            *key, period_end, value = row
            if value is None:
                continue
            label = " ".join(str(part) for part in key if part)
            data = series.setdefault(label, [0.0] * 12)
            data[period_end.month - 1] += float(value)
        return series


@register_lookups(prefix="ambiental_monthly_consumption", basename="ambientalmonthlyconsumptionchart")
class MonthlyConsumptionChart(AmbientalBaseChart, LineChart):

    def get_title(self):
        return {"display": True, "text": _("Monthly consumption")}

    def get_labels(self):
        self.series = self.monthly_series(
            "quantity", ["point__resource_type__description", "unit__description"]
        )
        return [str(month) for month in MONTHS]

    def get_datasets(self):
        return [self.dataset(label, data) for label, data in self.series.items()]


@register_lookups(prefix="ambiental_monthly_cost", basename="ambientalmonthlycostchart")
class MonthlyCostChart(AmbientalBaseChart, StackedBarChart):

    def get_title(self):
        return {"display": True, "text": _("Monthly cost by resource")}

    def get_labels(self):
        self.series = self.monthly_series("total_cost", ["point__resource_type__description"])
        return [str(month) for month in MONTHS]

    def get_datasets(self):
        return [self.dataset(label, data, fill=True) for label, data in self.series.items()]


@register_lookups(prefix="ambiental_building_ranking", basename="ambientalbuildingrankingchart")
class BuildingRankingChart(AmbientalBaseChart, HorizontalBarChart):
    """Edificios ordenados por su indicador del año (por defecto, agua por persona)."""

    def get_title(self):
        return {
            "display": True,
            "text": "%s: %s %s" % (_("Buildings ranking"), self.resource(), self.get_normalizer()),
        }

    def resource(self):
        return self.resource_type or Catalog.objects.filter(
            key=KEY_RESOURCE_TYPE, description=RESOURCE_WATER
        ).first()

    def get_normalizer(self):
        return self.normalizer or Catalog.objects.filter(
            key=KEY_NORMALIZER, description=NORMALIZER_PERSON
        ).first()

    def get_labels(self):
        start = datetime.date(self.year, 1, 1)
        end = datetime.date(self.year, 12, 31)
        buildings = Buildings.objects.filter(organization=self.organization)
        if self.building is not None:
            buildings = buildings.filter(pk=self.building.pk)
        ranking = []
        for building in buildings:
            result = compute_indicator(
                self.organization, building, self.resource(), self.get_normalizer(), start, end
            )
            if result["value"] is not None:
                ranking.append((building.name, float(result["value"])))
        ranking.sort(key=lambda item: item[1], reverse=True)
        self.data = [value for _name, value in ranking]
        return [name for name, _value in ranking]

    def get_datasets(self):
        return [self.dataset(_("Indicator"), self.data)]
