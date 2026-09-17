from django.urls import include, path
from rest_framework.routers import DefaultRouter

from presentation.platform import alerts_api, notifications_api, parameters_api, views

router = DefaultRouter()
router.register("systemparameter", parameters_api.SystemParameterViewSet, basename="api-systemparameter")
router.register(
    "notificationsetting", notifications_api.NotificationSettingViewSet, basename="api-notificationsetting"
)

router.register("alertrule", alerts_api.AlertRuleViewSet, basename="api-alertrule")
router.register("alertevent", alerts_api.AlertEventViewSet, basename="api-alertevent")

urlpatterns = [
    path("parameters/", views.systemparameter_list, name="systemparameter_list"),
    path("notifications/", views.notificationsetting_list, name="notificationsetting_list"),
    path("alerts/", views.alertrule_list, name="alertrule_list"),
    path("api/", include(router.urls)),
]
