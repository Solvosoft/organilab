from django_filters import DateTimeFilter, TypedMultipleChoiceFilter
from django_filters.rest_framework import FilterSet
from djgentelella.widgets.core import DateTimeInput

from pending_tasks.models import PendingTask


class PendingTaskFilterSet(FilterSet):
    creation_date = DateTimeFilter(
        widget=DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'})
    )
    status = TypedMultipleChoiceFilter(
        choices=PendingTask.STATUS, coerce=int
    )

    class Meta:
        model = PendingTask
        fields = {
            'id': ['exact'],
            'description': ['icontains'],
        }
