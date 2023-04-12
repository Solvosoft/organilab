from rest_framework.routers import DefaultRouter
from django.urls import path, include

from report.api.views import ReportDataViewSet

router = DefaultRouter()
router.register('api_report', ReportDataViewSet, basename='api-report')


app_name = 'report'


urlpatterns = [
    path('api/', include(router.urls)),
]