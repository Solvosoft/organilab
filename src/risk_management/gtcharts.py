from random import randint
from rest_framework import permissions
from django.db.models import Count, Sum, Q
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from djgentelella.chartjs import VerticalBarChart, HorizontalBarChart, \
    StackedBarChart, LineChart, PieChart, DoughnutChart, ScatterChart
from djgentelella.groute import register_lookups
from rest_framework.response import Response

from laboratory.models import Laboratory, SustanceCharacteristics, ShelfObject, Catalog, \
    Object, OrganizationStructure
from laboratory.utils_base_unit import get_conversion_units
from risk_management.api.serializer import RiskZoneSerializer
from risk_management.models import RiskZone, Buildings
from sga.models import DangerIndication

default_colors = ["229, 158, 64", "240, 180, 150", "0, 168, 150", "207, 130, 182",
                  "2, 128, 144", "1, 148, 147",
                  "240, 112, 96", "153, 235, 168", "241, 179, 167", "242, 137, 76",
                  "175, 151, 195",
                  "161, 178, 200",
                  "245, 216, 144", "216, 15, 53", "233, 175, 97", "4, 115, 143",
                  "162, 237, 133", "226, 148, 72",
                  "5, 102, 141", "241, 125, 90", "236, 194, 128", "220, 239, 133",
                  "242, 157, 175", "187, 141, 189",
                  "238, 186, 140", "238, 16, 58", "2, 195, 154", "121, 219, 172",
                  "239, 98, 104", "231, 167, 81"]


class BaseChart:
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    colors = default_colors

    def get_color(self):
        self.index = (self.index + 1) % len(self.colors)
        color_list = self.colors[self.index]
        color = 'rgb(' + color_list + ')'
        return color

    def get_extra_filters(self):
        serializer = RiskZoneSerializer(data=self.request.query_params)
        self.filters = {
            'in_where_laboratory__organization__pk': self.organization.pk,
            'object__type': '0'
        }
        laboratories=[]
        if serializer.is_valid():
            if 'risk_zone' in serializer.validated_data:
                risk_zones = [risk.pk for risk in serializer.validated_data['risk_zone']]
                risk_zone = RiskZone.objects.filter(pk__in=risk_zones, buildings__laboratories__isnull=False).values_list('buildings__laboratories__pk', flat=True)
                laboratories+= risk_zone

            if 'buildings' in serializer.validated_data:
                buildings = [building.pk for building in serializer.validated_data['buildings']]
                buildings = Buildings.objects.filter(pk__in=buildings, laboratories__isnull=False).values_list('laboratories__pk', flat=True)
                laboratories+= buildings

            self.filters['in_where_laboratory__pk__in'] = set(laboratories)


class LaboratoryPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perms(view.django_permissions_list)


@register_lookups(prefix="dangerIndication", basename="dangerindicationchart")
class LaboratoryDangerIndicationChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per Danger Indications')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        labels=[]
        self.data=[]
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()

        for dangerindication in DangerIndication.objects.all():
            amount=0
            for obj in queryset.filter(object__sustancecharacteristics__h_code=dangerindication):
                amount+= get_conversion_units(obj.measurement_unit,obj.quantity)
            if amount>0:
                labels.append(dangerindication.code)
                self.data.append(amount)

        if not labels:
            labels.append(_("No data registered"))
            self.data.append(0)
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        dataset=[ ]

        return [

            {'label': _('Count elements with code H'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]


@register_lookups(prefix="white_organ", basename="whiteorganchart")
class LaboratoryWhiteOrganChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per White Organ')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "white_organ").values('pk', 'description')
        labels = []
        self.data = []
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()

        for catalog in self.catalogs:
            amount = 0
            for obj in queryset.filter(
                object__sustancecharacteristics__white_organ__pk=catalog['pk']):
                amount += get_conversion_units(obj.measurement_unit, obj.quantity)
            if amount>0:
                labels.append(catalog['description'])
                self.data.append(amount)

        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [

            {'label': _('Count elements by White Organ'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]


@register_lookups(prefix="precursor_type", basename="precursortypechart")
class LaboratoryPrecursorTypeChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per Percursor Type')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "Precursor").values('pk', 'description')
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()
        labels = []
        self.data=[]

        for catalog in self.catalogs:
            amount=0
            for obj in queryset.filter(object__sustancecharacteristics__precursor_type__pk=catalog['pk']):
                amount+= get_conversion_units(obj.measurement_unit,obj.quantity)
            labels.append(catalog['description'])
            self.data.append(amount)

        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [

            {'label': _('Count elements by Precursor Type'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]

@register_lookups(prefix="nfpa", basename="nfpachart")
class LaboratoryNFPAChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per NFPA')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "nfpa").values('pk', 'description')
        self.data = []
        labels = []
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()

        for catalog in self.catalogs:
            amount=0
            for obj in queryset.filter(object__sustancecharacteristics__nfpa__pk=catalog['pk']):
                amount+= get_conversion_units(obj.measurement_unit,obj.quantity)
            labels.append(catalog['description'])
            self.data.append(amount)
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [

            {'label': _('Count elements by NFPA'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]



@register_lookups(prefix="ue_code", basename="uecodechart")
class LaboratoryUECodeChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per UE Code')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "ue_code").values('pk', 'description')
        self.aggrateparams = {}
        labels = []
        self.data=[]
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()

        for catalog in self.catalogs:
            amount=0
            for obj in queryset.filter(object__sustancecharacteristics__ue_code__pk=catalog['pk']):
                amount+= get_conversion_units(obj.measurement_unit,obj.quantity)
            labels.append(catalog['description'])
            self.data.append(amount)

        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [

            {'label': _('Count elements by UE Code'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]



@register_lookups(prefix="storage_class", basename="storageclasschart")
class LaboratoryStorageClassChart(BaseChart, HorizontalBarChart):
    permission_classes = [LaboratoryPermission]
    django_permissions_list = ['risk_management.view_riskzone']

    def get_title(self):
        return {'display': True,
                'text': _('Sustances per Storage Class')
                }

    def list(self, request):
        raise Http404("Not found")


    def retrieve(self, request, pk):
        self.request = request
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "storage_class").values('pk', 'description')
        self.data=[]
        labels = []
        self.get_extra_filters()
        queryset=ShelfObject.objects.filter(**self.filters).distinct()
        for catalog in self.catalogs:
            amount=0
            for obj in queryset.filter(object__sustancecharacteristics__storage_class__pk=catalog['pk']):
                amount+= get_conversion_units(obj.measurement_unit,obj.quantity)
            labels.append(catalog['description'])
            self.data.append(amount)

        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        return [

            {'label': _('Count elements by Storage Class'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]
