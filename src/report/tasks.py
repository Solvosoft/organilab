import importlib

from django.conf import settings

from report.models import TaskReport
from report.utils import document_status
from report.views.base import build_report
from django.utils import translation
from django.utils.translation import gettext as _
from celery.utils.log import get_task_logger

app = importlib.import_module(settings.CELERY_MODULE).app
logger = get_task_logger("organilab_celery")


@app.task()
def task_report(pk, absolute_uri):
    try:
        build_report(pk, absolute_uri)
    except Exception:
        logger.exception("Report task failed (pk=%s)", pk)
        report = TaskReport.objects.filter(pk=pk).first()
        if report is not None:
            with translation.override(report.language):
                document_status(report, _("Error generating the report"))
        raise
