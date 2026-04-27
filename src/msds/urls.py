from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.api import SDSTraceabilityViewSet
from .views import (
    get_list_msds,
    index_msds,
    sds_create,
    regulation_view,
    download_all_regulations,
    verified_sds,
)

router = DefaultRouter()
router.register(
    "api_sds_traceability", SDSTraceabilityViewSet, basename="api-sds-traceability"
)

urlpatterns = [
    path("api/", include(router.urls)),
    path("index_msds/", index_msds, name="index_msds"),
    path("sds/create/", sds_create, name="sds_create"),
    path("list/", get_list_msds, name="list_msds"),
    path("verified_sds/", verified_sds, name="verified_sds"),
    path("api/sds/", include(router.urls)),
]

regulation_urlpath = [
    path("regulations/", regulation_view, name="regulation_docs"),
    path(
        "regulations/download/all",
        download_all_regulations,
        name="download_all_regulations",
    ),
]
