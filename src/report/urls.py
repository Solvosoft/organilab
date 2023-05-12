from rest_framework.routers import DefaultRouter
from django.urls import path, include

from report.api.views import ReportDataViewSet
from report.views import base


base_reports = [
    path('create/', base.create_request_by_report, name='create_report_request'),
    path('download/', base.download_report, name='generate_report'),
    path('table/<int:pk>/', base.report_table, name='report_table'),
    path('status/', base.report_status, name="report_status"),
]

router = DefaultRouter()
router.register('api_report', ReportDataViewSet, basename='api-report')


app_name = 'report'


urlpatterns = [
    path('api/', include(router.urls)),
    path('<int:org_pk>/<int:lab_pk>/', include(base_reports))
]