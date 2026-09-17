from django.urls import include, path
from rest_framework.routers import DefaultRouter

from presentation.platform import notifications_api, parameters_api, views

router = DefaultRouter()
router.register("systemparameter", parameters_api.SystemParameterViewSet, basename="api-systemparameter")
router.register(
    "notificationsetting", notifications_api.NotificationSettingViewSet, basename="api-notificationsetting"
)

urlpatterns = [
    path("parameters/", views.systemparameter_list, name="systemparameter_list"),
    path("notifications/", views.notificationsetting_list, name="notificationsetting_list"),
    path("api/", include(router.urls)),
]
