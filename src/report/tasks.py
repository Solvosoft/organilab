import importlib

from django.conf import settings

from report.views.base import build_report
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
app = importlib.import_module(settings.CELERY_MODULE).app


@app.task()
def task_report(pk, absolute_uri):
    try:
        build_report(pk, absolute_uri)
    except Exception:
        raise ObjectDoesNotExist(_("Object doesn't exists"))