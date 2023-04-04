from django.conf import settings
import importlib

from laboratory.models import TaskReport
from report.views.lab_room import lab_room_html, lab_room_pdf

app = importlib.import_module(settings.CELERY_MODULE).app

@app.task()
def laboratory_room_report(pk):
    report = TaskReport.objects.filter(pk=pk).first()
    if report.file_type=='html':
        lab_room_html(report)
    elif report.file_type=='pdf':
        lab_room_pdf(report)