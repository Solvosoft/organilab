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

from laboratory.models import Laboratory, SustanceCharacteristics, ShelfObject, Catalog
from risk_management.models import RiskZone
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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        labels=[]
        self.data=[]
        print(self.request.GET["unit"])
        unit_filters = {}
        if self.request.GET["unit"] == "Litros":
            unit_filters["measurement_unit__pk__in"] = [62,63]
        elif self.request.GET["unit"] == "Kilogramos":
            unit_filters["measurement_unit__pk__in"] = [66,67,65]
        elif self.request.GET["unit"] == "Metros":
            unit_filters["measurement_unit__pk__in"] = [59,60,61]
        else:
            unit_filters["measurement_unit__description"] = Catalog.objects.get(description=self.request.GET["unit"])
        sc=SustanceCharacteristics.objects.filter(obj__shelfobject__in_where_laboratory=self.laboratory)
        queryset = DangerIndication.objects.filter(sustancecharacteristics__in=sc)
#        queryset = DangerIndication.objects.annotate(sc_count=Sum('sustancecharacteristics__obj__shelfobject')).filter(sustancecharacteristics__in=sc)


#        self.unidad = set(DangerIndication.objects.filter(sustancecharacteristics__in=sc).values_list(
#            'sustancecharacteristics__obj__shelfobject__measurement_unit__description', flat=True))
        for dangerindication in queryset:
            shelf_object = ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__h_code=dangerindication, **unit_filters).aggregate(total = Sum("quantity_base_unit", default=0))
            labels.append(dangerindication.code)
            self.data.append(shelf_object["total"])

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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "white_organ").values('pk', 'description')
        self.aggrateparams = {}
        self.data = []
        labels = []
        for catalog in self.catalogs:
            labels.append(catalog['description'])
            self.data.append(ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__white_organ=catalog["pk"]).aggregate(total = Sum("quantity_base_unit", default=0))["total"])
            self.aggrateparams["c%d"%catalog['pk']]  = Count('object__sustancecharacteristics', filter=Q(
                object__sustancecharacteristics__white_organ= catalog['pk']
            ))
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        data = []
        dataset = ShelfObject.objects.filter(in_where_laboratory=self.laboratory).aggregate(**self.aggrateparams)
        for catalog in self.catalogs:
            data.append(dataset['c%d'%catalog['pk']])
        #
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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "Precursor").values('pk', 'description')
        self.aggrateparams = {}
        self.data = []
        labels = []
        for catalog in self.catalogs:
            labels.append(catalog['description'])
            self.data.append(ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__precursor_type=catalog["pk"]).aggregate(total = Sum("quantity_base_unit", default=0))["total"])

            self.aggrateparams["c%d"%catalog['pk']]  = Count('object__sustancecharacteristics', filter=Q(
                object__sustancecharacteristics__precursor_type= catalog['pk']
            ))
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        data = []
        dataset = ShelfObject.objects.filter(in_where_laboratory=self.laboratory).aggregate(**self.aggrateparams)
        for catalog in self.catalogs:
            data.append(dataset['c%d'%catalog['pk']])
        #
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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "nfpa").values('pk', 'description')
        self.aggrateparams = {}
        labels = []
        self.data = []
        for catalog in self.catalogs:
            labels.append(catalog['description'])
            self.data.append(ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__nfpa__pk=catalog["pk"]).aggregate(total = Sum("quantity_base_unit", default=0))["total"])

            self.aggrateparams["c%d"%catalog['pk']]  = Count('object__sustancecharacteristics', filter=Q(
                object__sustancecharacteristics__nfpa= catalog['pk']
            ))
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        data = []
        dataset = ShelfObject.objects.filter(in_where_laboratory=self.laboratory).aggregate(**self.aggrateparams)
        for catalog in self.catalogs:
            data.append(dataset['c%d'%catalog['pk']])
        #
        return [

            {'label': _('Count elements by NFPA'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': data
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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "ue_code").values('pk', 'description')
        self.aggrateparams = {}
        labels = []
        self.data = []
        for catalog in self.catalogs:
            labels.append(catalog['description'])
            self.data.append(ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__ue_code=catalog["pk"]).aggregate(total = Sum("quantity_base_unit", default=0))["total"])

            self.aggrateparams["c%d"%catalog['pk']]  = Count('object__sustancecharacteristics', filter=Q(
                object__sustancecharacteristics__ue_code= catalog['pk']
            ))
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        data = []
        dataset = ShelfObject.objects.filter(in_where_laboratory=self.laboratory).aggregate(**self.aggrateparams)
        for catalog in self.catalogs:
            data.append(dataset['c%d'%catalog['pk']])
        #
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
        self.laboratory = get_object_or_404(Laboratory, pk=pk)
        data = self.get_graph_data()
        serializer = self.serializer_class(data)
        return Response(serializer.data)


    def get_labels(self):
        self.catalogs = Catalog.objects.filter(key = "storage_class").values('pk', 'description')
        self.aggrateparams = {}
        self.data = []
        labels = []
        for catalog in self.catalogs:
            labels.append(catalog['description'])
            self.data.append(ShelfObject.objects.filter(in_where_laboratory = self.laboratory, object__sustancecharacteristics__storage_class=catalog["pk"]).aggregate(total = Sum("quantity_base_unit", default=0))["total"])

            self.aggrateparams["c%d"%catalog['pk']]  = Count('object__sustancecharacteristics', filter=Q(
                object__sustancecharacteristics__storage_class= catalog['pk']
            ))
        return labels


    def get_datasets(self):
        self.index = randint(0, len(self.colors))
        data = []
        dataset = ShelfObject.objects.filter(in_where_laboratory=self.laboratory).aggregate(**self.aggrateparams)
        for catalog in self.catalogs:
            data.append(dataset['c%d'%catalog['pk']])
        #
        return [

            {'label': _('Count elements by Storage Class'),
             'backgroundColor': self.get_color(),
             'borderColor': self.get_color(),
             'borderWidth': 1,
             'data': self.data
             }
                ]
