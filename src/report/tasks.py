import importlib

from django.conf import settings

from report.views.base import build_report

app = importlib.import_module(settings.CELERY_MODULE).app


@app.task()
def task_report(pk, absolute_uri):
    build_report(pk, absolute_uri)
