from django.urls import re_path, path, include
from rest_framework.routers import DefaultRouter
from reservations_management.api.views import (
    ApiReservedProductsCRUD,
    ApiListReservationReservedProduct, ReservedProductViewSet
)

from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'reservations_management'
router = DefaultRouter()
router.register('reservedproducttableview', ReservedProductViewSet, 'api-reservedproduct')

urlpatterns = [
    re_path(r'rm/api/reservedproduct/(?P<pk>\d+)/', ApiReservedProductsCRUD.as_view(),
            name='api_reservation_management'),
    re_path(r'rm/api/reservationreservedproducts/(?P<pk>\d+)/list', ApiListReservationReservedProduct.as_view(),
            name='api_reservation_products_list'),

]

urlpatterns = format_suffix_patterns(urlpatterns)
urlpatterns = urlpatterns + [path('managementreserveationsapi/', include(router.urls))]
