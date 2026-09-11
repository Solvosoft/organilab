from django.contrib.auth.models import User
from django_filters import FilterSet, CharFilter

from laboratory.models import Laboratory, OrganizationStructureRelations


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = {
            "first_name": ["icontains"],
            "last_name": ["icontains"],
            "username": ["icontains"],
            "email": ["icontains"],
        }


class OrganizationStructureRelationsFilter(FilterSet):
    """
    Filter for OrganizationStructureRelations that allows filtering by laboratory name.
    """
    laboratory_name = CharFilter(method="filter_laboratory_name")

    class Meta:
        model = OrganizationStructureRelations
        fields = ["laboratory_name"]

    def filter_laboratory_name(self, queryset, name, value):
        """
        Filter by laboratory name using the object_id field.
        """
        if not value:
            return queryset

        # Get laboratory IDs that match the search
        lab_ids = Laboratory.objects.filter(
            name__icontains=value
        ).values_list("pk", flat=True)

        return queryset.filter(object_id__in=lab_ids)
