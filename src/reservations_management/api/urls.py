from django.urls import path
from django.conf.urls import url
from reservations_management.api.views import (
   ApiReservedProductsCRUD,
)

from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'reservations_management'

urlpatterns = [
    url(r'rm/api/reservedproduct/(?P<pk>\d+)/', ApiReservedProductsCRUD.as_view(), name='api_reservation_management'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
