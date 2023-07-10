import importlib

from django.conf import settings

from report.views.base import build_report
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from celery.utils.log import get_task_logger

app = importlib.import_module(settings.CELERY_MODULE).app
logger = get_task_logger("organilab_celery")

@app.task()
def task_report(pk, absolute_uri):
    try:
        build_report(pk, absolute_uri)
    except Exception as e:
        logger.error(str(e))
        raise ObjectDoesNotExist(_("Object doesn't exists"))

