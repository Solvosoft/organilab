from rest_framework.routers import DefaultRouter
from django.urls import path, include

from report.api.views import ReportDataViewSet
from report.views import base


celery_reports = [
    path('reports/create/', base.create_request_by_report, name='create_report_request'),
    path('reports/<int:org_pk>', base.download_report, name='generate_report'),
    path('reports/table/<int:org_pk>/<int:pk>', base.report_table, name='report_table'),

]

router = DefaultRouter()
router.register('api_report', ReportDataViewSet, basename='api-report')


app_name = 'report'


urlpatterns = [
    path('api/', include(router.urls)),
    path('reports/status/', base.report_status, name="report_status"),
    path('celery/<int:lab_pk>/', include(celery_reports))
]