from django_filters import FilterSet

from risk_management.models import Buildings


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
