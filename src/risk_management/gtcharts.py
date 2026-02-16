import logging
from django.utils import timezone
from random import randint

from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from djgentelella.chartjs import (
    HorizontalBarChart,
)
from djgentelella.groute import register_lookups
from rest_framework.response import Response

from laboratory.models import (
    ShelfObject,
    Catalog,
    OrganizationStructure, BaseUnitValues,
)
from laboratory.utils_base_unit import get_conversion_units
from risk_management.api.serializer import RiskZoneSerializer
from risk_management.models import RiskZone, Buildings, EstablishmentLogs
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
logger = logging.getLogger("organilab")


class BaseChart:
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    colors = default_colors

    def get_color(self):
        self.index = (self.index + 1) % len(self.colors)
        color_list = self.colors[self.index]
        color = "rgb(" + color_list + ")"
        return color

    def get_extra_filters(self):
        serializer = RiskZoneSerializer(data=self.request.query_params)
        self.filters = {
            "in_where_laboratory__organization__pk": self.organization.pk,
            "object__type": "0",
        }
        self.no_labs = False
        laboratories = []
        if serializer.is_valid():
            has_filter = False
            if "risk_zone" in serializer.validated_data:
                risk_zones = [
                    risk.pk for risk in serializer.validated_data["risk_zone"]
                ]
                risk_zone = RiskZone.objects.filter(
                    pk__in=risk_zones, buildings__laboratories__isnull=False
                ).values_list("buildings__laboratories__pk", flat=True)
                laboratories += risk_zone
                has_filter = True
            if "buildings" in serializer.validated_data:
                buildings = [
                    building.pk for building in serializer.validated_data["buildings"]
                ]
                buildings = Buildings.objects.filter(
                    pk__in=buildings, laboratories__isnull=False
                ).values_list("laboratories__pk", flat=True)
                laboratories += buildings
                has_filter = True
            if has_filter:
                if len(laboratories) > 0:
                    self.filters["in_where_laboratory__pk__in"] = list(
                        set(laboratories)
                    )
                else:
                    del self.filters["in_where_laboratory__organization__pk"]
                    self.no_labs = True


class LaboratoryPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perms(view.django_permissions_list)

@register_lookups(prefix="dangerIndication", basename="dangerindicationchart")
class LaboratoryDangerIndicationChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per Danger Indications")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        labels = []
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []
        self.liquid_data_total = 0
        self.get_extra_filters()

        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()

        for dangerindication in DangerIndication.objects.all():
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__h_code=dangerindication
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                     kilo_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                          obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(dangerindication.code)
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]


@register_lookups(prefix="white_organ", basename="whiteorganchart")
class LaboratoryWhiteOrganChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per White Organ")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key="white_organ").values(
            "pk", "description"
        )
        labels = []
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []
        self.get_extra_filters()

        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()

        for catalog in self.catalogs:
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__white_organ__pk=catalog["pk"]
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                    kilo_amount += get_conversion_units(obj.measurement_unit,
                                                        obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(catalog["description"])
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]


@register_lookups(prefix="precursor_type", basename="precursortypechart")
class LaboratoryPrecursorTypeChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per Percursor Type")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key="Precursor").values(
            "pk", "description"
        )
        self.get_extra_filters()
        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()
        labels = []
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []

        for catalog in self.catalogs:
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__precursor_type__pk=catalog["pk"]
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                    kilo_amount += get_conversion_units(obj.measurement_unit,
                                                        obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(catalog["description"])
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]


@register_lookups(prefix="nfpa", basename="nfpachart")
class LaboratoryNFPAChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per NFPA")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key="nfpa").values("pk", "description")
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []
        labels = []
        self.get_extra_filters()
        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()

        for catalog in self.catalogs:
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__nfpa__pk=catalog["pk"]
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                    kilo_amount += get_conversion_units(obj.measurement_unit,
                                                        obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(catalog["description"])
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]


@register_lookups(prefix="ue_code", basename="uecodechart")
class LaboratoryUECodeChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per UE Code")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key="ue_code").values(
            "pk", "description"
        )
        self.aggrateparams = {}
        labels = []
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []
        self.get_extra_filters()
        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()

        for catalog in self.catalogs:
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__ue_code__pk=catalog["pk"]
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                    kilo_amount += get_conversion_units(obj.measurement_unit,
                                                        obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(catalog["description"])
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]


@register_lookups(prefix="storage_class", basename="storageclasschart")
class LaboratoryStorageClassChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Sustances per Storage Class")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                }
            }
        }
        return options

    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key="storage_class").values(
            "pk", "description"
        )
        self.litro_data = []
        self.kilo_data = []
        self.libra_data = []
        labels = []
        self.get_extra_filters()
        queryset = ShelfObject.objects.filter(**self.filters).distinct()
        if self.no_labs:
            queryset = queryset.none()

        for catalog in self.catalogs:
            litro_amount = 0
            kilo_amount = 0
            libra_amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__storage_class__pk=catalog["pk"]
            ):
                base_unit = BaseUnitValues.objects.filter(
                    measurement_unit=obj.measurement_unit).first()
                if base_unit and base_unit.measurement_unit_base.description == "Kilogramos":
                    kilo_amount += get_conversion_units(obj.measurement_unit,
                                                        obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Litros":
                    litro_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                elif base_unit and base_unit.measurement_unit_base.description == "Libra":
                    libra_amount += get_conversion_units(obj.measurement_unit,
                                                         obj.quantity)
                else:
                    logger.error(
                        f"Error in base unit {obj.measurement_unit}, obj: {obj.pk}")

            if litro_amount > 0 or kilo_amount > 0 or libra_amount > 0:
                labels.append(catalog["description"])
                self.litro_data.append(round(float(litro_amount), 2))
                self.kilo_data.append(round(float(kilo_amount), 2))
                self.libra_data.append(round(float(libra_amount), 2))

        if not labels:
            labels.append(_("No data registered"))
            self.litro_data.append(0)
            self.kilo_data.append(0)
            self.libra_data.append(0)
        return labels

    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()
        return [
            {
                "label": _("Litro (L)"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": self.litro_data,
            },
            {
                "label": _("Kilogramo (Kg)"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": self.kilo_data,
            },
            {
                "label": _("Libra (Lb)"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": self.libra_data,
            }
        ]

@register_lookups(prefix="eslo", basename="eslochart")
class EstablishmentLogsClassChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ["risk_management.view_riskzone"]

    def get_title(self):
        return {"display": True, "text": _("Risk Categories Summary")}

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        self.pk = request.GET.get('zone_pk')
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    def get_options(self):
        options = super().get_options()
        options['plugins'] = {
            'showDataLabels': True,
            'datalabels': {
                'anchor': 'end',
                'align': 'end',
                'offset': 4,
                'clip': False,
                'color': '#333',
                'font': {
                    'weight': 'bold',
                    'size': 11
                },
            }
        }
        return options

    def get_scales(self):
        return {
            'xAxes': [{
                'ticks': {
                    'min': 0,
                    'max': 1,
                    'stepSize': 0.1
                }
            }],
            'yAxes': [{
                'ticks': {}
            }]
        }

    def get_labels(self):
        return [""]

    def get_datasets(self):
        today = timezone.now().date()
        latest_log = EstablishmentLogs.objects.filter(
            object_id=self.pk,
            content_type=ContentType.objects.get_for_model(RiskZone),
            date__date=today
        ).order_by('-date').first()

        if not latest_log:
            latest_log = EstablishmentLogs.objects.filter(
                object_id=self.pk,
                content_type=ContentType.objects.get_for_model(RiskZone)
            ).order_by('-date').first()

        physical_value = latest_log.physical if latest_log else 0
        health_value = latest_log.health if latest_log else 0
        environmental_value = latest_log.environmental if latest_log else 0

        self.index = randint(0, len(self.colors) - 1)
        color_1 = self.get_color()
        color_2 = self.get_color()
        color_3 = self.get_color()

        return [
            {
                "label": _("Physical"),
                "backgroundColor": color_1,
                "borderColor": color_1,
                "borderWidth": 1,
                "data": [physical_value],
            },
            {
                "label": _("Health"),
                "backgroundColor": color_2,
                "borderColor": color_2,
                "borderWidth": 1,
                "data": [health_value],
            },
            {
                "label": _("Environmental"),
                "backgroundColor": color_3,
                "borderColor": color_3,
                "borderWidth": 1,
                "data": [environmental_value],
            }
        ]
