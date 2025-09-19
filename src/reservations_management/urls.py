"""organilab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import include
from django.urls import path

from .views import (
    ReservationsListView,
    ManageReservationView,
)

from .functions import (
    get_product_name_and_quantity,
    validate_reservation,
    increase_stock,
)

urlpatterns = [
    path(
        "reservations/<int:pk>/manage/",
        ManageReservationView.as_view(),
        name="manage_reservation",
    ),
    path(
        "reservations/list/<int:status>/",
        ReservationsListView.as_view(),
        name="reservations_list",
    ),
    # Functions URLs
    path(
        "reservedproduct/get_product_name_and_quantity/",
        get_product_name_and_quantity,
        name="get_product_name_and_quantity",
    ),
    path(
        "reservedproduct/validate_reservation/",
        validate_reservation,
        name="validate_reservation",
    ),
    path("reservedproduct/increase_stock/", increase_stock, name="increase_stock"),
]
