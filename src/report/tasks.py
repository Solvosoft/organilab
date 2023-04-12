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
    build_report(pk)

@app.task()
def object_log_change_report(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_objectlogchange_html(report)
    elif report.file_type=='pdf':
        report_objectlogchange_pdf(report)
    else:
        report_objectlogchange_doc(report)

@app.task()
def report_reactive_precursor(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_reactive_precursor_html(report)
    elif report.file_type=='pdf':
        report_reactive_precursor_pdf(report)
    else:
        report_reactive_precursor_doc(report)

@app.task()
def report_objects(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_objects_html(report)
    elif report.file_type == 'pdf':
        report_objects_pdf(report)
    else:
        report_object_doc(report)
@app.task()
def report_limit_objects(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_limit_object_html(report)
    elif report.file_type == 'pdf':
        report_limit_object_pdf(report)
    else:
        report_limit_object_doc(report)

@app.task()
def report_organization_reactive_list(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_organization_reactive_list_html(report)
    elif report.file_type == 'pdf':
        report_organization_reactive_list_pdf(report)
    else:
        report_organization_reactive_list_doc(report)