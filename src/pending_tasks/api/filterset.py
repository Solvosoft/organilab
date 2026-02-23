from django_filters import ChoiceFilter, DateTimeFilter
from django_filters.rest_framework import FilterSet
from djgentelella.widgets.core import DateTimeInput

from pending_tasks.models import PendingTask

class PendingTaskFilterSet(FilterSet):
    creation_date = DateTimeFilter(
        widget=DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM:SS'})
    )
    status = ChoiceFilter(choices=PendingTask.STATUS)
    class Meta:
        model = PendingTask
        fields = {
            'id': ['exact'],
            'description': ['icontains'],
        }
