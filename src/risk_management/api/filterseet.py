from django_filters import FilterSet

from risk_management.models import Buildings, Structure


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
