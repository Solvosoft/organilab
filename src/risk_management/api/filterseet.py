from django_filters import FilterSet, DateFromToRangeFilter
from djgentelella.fields.drfdatetime import DateRangeTextWidget

from risk_management.models import Buildings, Structure, IncidentReport, Regent


class BuildingFilter(FilterSet):


    class Meta:
        model = Buildings
        fields = {
                    'name': ['icontains'],
                    'laboratories': ['exact'],
                    'nearby_buildings': ['exact'],
                    'manager': ['exact'],
                    'regents': ['exact'],
                  }

class StructureFilter(FilterSet):


    class Meta:
        model = Structure
        fields = {
                    'name': ['icontains'],
                    'buildings': ['exact'],
                    'manager': ['exact'],
                    'type_structure': ['exact'],
                  }

class IncidentReportFilter(FilterSet):
    incident_date = DateFromToRangeFilter(
        widget=DateRangeTextWidget(attrs={"placeholder": "DD/MM/YYYY/"})
    )

    class Meta:
        model = IncidentReport
        fields = {
                    'short_description': ['icontains'],
                    'buildings': ['exact'],
                    'laboratories': ['exact'],
                  }

class RegentFilter(FilterSet):

    class Meta:
        model = Regent
        fields = {
                    'user': ['exact'],
                    'laboratories': ['exact'],
                  }
