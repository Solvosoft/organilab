from django.conf import settings
import importlib

from laboratory.models import TaskReport
from report.views.lab_room import lab_room_html, lab_room_pdf
from report.views.objects import report_objectlogchange_html, report_objectlogchange_pdf, report_objectlogchange_doc

app = importlib.import_module(settings.CELERY_MODULE).app

@app.task()
def laboratory_room_report(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        lab_room_html(report)
    elif report.file_type=='pdf':
        lab_room_pdf(report)

@app.task()
def object_log_change_report(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        report_objectlogchange_html(report)
    elif report.file_type=='pdf':
        report_objectlogchange_pdf(report)
    else:
        report_objectlogchange_doc(report)