from random import randint
from rest_framework import permissions
from django.db.models import Count, Sum, Q, Max, DecimalField
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from djgentelella.chartjs import (
    VerticalBarChart,
    HorizontalBarChart,
    StackedBarChart,
    LineChart,
    PieChart,
    DoughnutChart,
    ScatterChart,
)
from djgentelella.groute import register_lookups
from rest_framework.response import Response

from laboratory.api.serializers import ReactiveLimitSerializer, ReactiveLimitsSerializer
from laboratory.models import (
    Laboratory,
    SustanceCharacteristics,
    ShelfObject,
    Catalog,
    Object,
    OrganizationStructure, ReactiveLimit, ObjectMaximumLimit,
)
from laboratory.utils_base_unit import get_conversion_units
from risk_management.api.serializer import RiskZoneSerializer
from risk_management.models import RiskZone, Buildings
from sga.models import DangerIndication

default_colors = [
    "229, 158, 64",
    "240, 180, 150",
    "0, 168, 150",
    "207, 130, 182",
    "2, 128, 144",
    "1, 148, 147",
    "240, 112, 96",
    "153, 235, 168",
    "241, 179, 167",
    "242, 137, 76",
    "175, 151, 195",
    "161, 178, 200",
    "245, 216, 144",
    "216, 15, 53",
    "233, 175, 97",
    "4, 115, 143",
    "162, 237, 133",
    "226, 148, 72",
    "5, 102, 141",
    "241, 125, 90",
    "236, 194, 128",
    "220, 239, 133",
    "242, 157, 175",
    "187, 141, 189",
    "238, 186, 140",
    "238, 16, 58",
    "2, 195, 154",
    "121, 219, 172",
    "239, 98, 104",
    "231, 167, 81",
]


class BaseChart:
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    colors = default_colors

    def get_color(self):
        self.index = (self.index + 1) % len(self.colors)
        color_list = self.colors[self.index]
        color = "rgb(" + color_list + ")"
        return color

    def get_extra_filters(self):
        serializer = ReactiveLimitSerializer(data=self.request.query_params)
        self.filters = {}
        self.no_labs = False
        laboratories = []
        if serializer.is_valid():
            self.filters["created_at"] = serializer.validated_data["created_at"]
            self.filters["object__pk__in"] = serializer.validated_data["object"]
            self.filters["laboratory__pk"] = serializer.validated_data["laboratory"]

class LaboratoryPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perms(view.django_permissions_list)


@register_lookups(prefix="objectlimits", basename="objectlimitschart")
class ObjectLimitsClassChart(BaseChart, LineChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["laboratory.view_object"]
    obj = ""

    def get_title(self):
        return {"display": True, "text": _("Monthly limit history %s")%self.obj}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.laboratory = get_object_or_404(Laboratory, pk=self.request.query_params.get("laboratory", None))
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_extra_filters(self):
        data = self.request.query_params.copy()
        serializer = ReactiveLimitsSerializer(data=data, context={"lab_pk": self.laboratory.pk})
        self.filters = {}
        if serializer.is_valid():
            if "object" in serializer.validated_data and "years" in serializer.validated_data:
                self.filters["laboratory__pk"] = serializer.validated_data["laboratory"].pk
                if "object" in serializer.validated_data:
                    self.filters["object__pk"] = serializer.validated_data["object"].pk
                if "years" in serializer.validated_data:
                    self.filters["created_at__year"] = serializer.validated_data["years"]

    def get_labels(self):
        queryset = ObjectMaximumLimit.objects.all()
        self.data = []
        labels = []
        self.get_extra_filters()
        if self.filters:
            queryset = queryset.filter(**self.filters).distinct()
            self.obj = queryset.first()
            self.obj = f"{self.obj.object.name} ({self.obj.measurement_unit.description})"
        else:
            queryset = queryset.none()

        months = ((1, _("January")), (2, _("February")), (3, _("March")), (4, _("April")), (5, _("May")),
                  (6, _("June")), (7, _("July")), (8, _("August")), (9, _("September")), (10, _("October")),
                  (11, _("November")), (12, _("December")))
        for month in months:
            quantity = queryset.filter(created_at__month=month[0]).aggregate(Max('quantity', default=0, output_field=DecimalField()))
            labels.append(month[1])
            self.data.append(quantity['quantity__max'])

        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [
            {
                "label": _("Quantity"),
                "backgroundColor": self.get_color(),
                "borderColor": self.get_color(),
                "borderWidth": 1,
                "data": self.data,
            }
        ]
