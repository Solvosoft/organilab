from random import randint

from django.db.models import Count, Sum
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.shortcuts import get_object_or_404
from djgentelella.chartjs import VerticalBarChart, HorizontalBarChart, \
    StackedBarChart, LineChart, PieChart, DoughnutChart, ScatterChart
from djgentelella.groute import register_lookups
from rest_framework.response import Response

from laboratory.models import Laboratory, SustanceCharacteristics
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
    colors = default_colors

    def get_color(self):
        self.index = (self.index + 1) % len(self.colors)
        color_list = self.colors[self.index]
        color = 'rgb(' + color_list + ')'
        return color



@register_lookups(prefix="dangerIndication", basename="dangerindicationchart")
class LaboratoryDangerIndicationChart(BaseChart, HorizontalBarChart):

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
        sc=SustanceCharacteristics.objects.filter(obj__shelfobject__in_where_laboratory=self.laboratory)
        queryset = DangerIndication.objects.annotate(sc_count=Count('sustancecharacteristics')).filter(sustancecharacteristics__in=sc)
#        queryset = DangerIndication.objects.annotate(sc_count=Sum('sustancecharacteristics__obj__shelfobject')).filter(sustancecharacteristics__in=sc)


#        self.unidad = set(DangerIndication.objects.filter(sustancecharacteristics__in=sc).values_list(
#            'sustancecharacteristics__obj__shelfobject__measurement_unit__description', flat=True))
        for dangerindication in queryset:
            labels.append(dangerindication.code)
            self.data.append(dangerindication.sc_count)

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
