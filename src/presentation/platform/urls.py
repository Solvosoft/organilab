from django.urls import include, path
from rest_framework.routers import DefaultRouter

from presentation.platform import parameters_api, views

router = DefaultRouter()
router.register("systemparameter", parameters_api.SystemParameterViewSet, basename="api-systemparameter")

urlpatterns = [
    path("parameters/", views.systemparameter_list, name="systemparameter_list"),
    path("api/", include(router.urls)),
]
