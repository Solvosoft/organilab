from rest_framework.routers import DefaultRouter
from django.urls import path, include

from report.api.views import ReportDataViewSet, ReportDataLogViewSet
from report.views import base


base_reports = [
    path('create/', base.create_request_by_report, name='create_report_request'),
    path('download/', base.download_report, name='generate_report'),
    path('table/<int:pk>/', base.report_table, name='report_table'),
    path('status/', base.report_status, name="report_status"),
]
base_organization_reports = [
    path('create/organization/', base.create_organization_request_by_report, name='create_organization_report_request'),
    path('download/organization/', base.download__organization_report, name='generate_organization_report'),
]

router = DefaultRouter()
router.register('api_report', ReportDataViewSet, basename='api-report')
router.register('api_report_log', ReportDataLogViewSet, basename='api-report-log')


app_name = 'report'


urlpatterns = [
    path('api/', include(router.urls)),
    path('<int:org_pk>/<int:lab_pk>/', include(base_reports)),
    path('<int:org_pk>/', include(base_organization_reports))
]
