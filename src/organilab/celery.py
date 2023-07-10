import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'organilab.settings')
app = Celery('organilab')

app.config_from_object('django.conf:settings')


# ====== Magic starts
from celery.signals import setup_logging

@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)
# ===== Magic ends

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
