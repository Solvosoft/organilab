import importlib

from django.conf import settings

from laboratory.models import TaskReport
from report.views.base import build_report
from report.views.objects import report_objectlogchange_html, report_objectlogchange_pdf, report_objectlogchange_doc \
    , report_reactive_precursor_html, report_reactive_precursor_pdf, report_reactive_precursor_doc \
    , report_objects_html, report_object_doc, report_objects_pdf \
    , report_limit_object_html, report_limit_object_pdf, report_limit_object_doc, \
    report_organization_reactive_list_html, report_organization_reactive_list_pdf, report_organization_reactive_list_doc

app = importlib.import_module(settings.CELERY_MODULE).app


@app.task()
def task_report(pk):
    try:
        build_report(pk)
    except:
        pass
