from django.urls import path

from .views import get_list_msds, index_msds, sds_create, regulation_view, download_all_regulations

urlpatterns = [
    path("index_msds/", index_msds, name="index_msds"),
    path("sds/create/", sds_create, name="sds_create"),
    path("list/", get_list_msds, name="list_msds"),
]

regulation_urlpath = [
    path("regulations/", regulation_view, name="regulation_docs"),
    path(
        "regulations/download/all",
        download_all_regulations,
        name="download_all_regulations",
    ),
]
