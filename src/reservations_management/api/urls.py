from django.urls import re_path

from reservations_management.api.views import (
   ApiReservedProductsCRUD,
   ApiListReservationReservedProduct
)

from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'reservations_management'

urlpatterns = [
    re_path(r'rm/api/reservedproduct/(?P<pk>\d+)/', ApiReservedProductsCRUD.as_view(), name='api_reservation_management'),
    re_path(r'rm/api/reservationreservedproducts/(?P<pk>\d+)/list', ApiListReservationReservedProduct.as_view(), name='api_reservation_products_list'),

]

urlpatterns = format_suffix_patterns(urlpatterns)
