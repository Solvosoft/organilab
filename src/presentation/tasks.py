from django.conf import settings
import importlib
from django.core.management import call_command
app = importlib.import_module(settings.CELERY_MODULE).app

@app.task()
def clean_session():
    call_command('clearsessions')

@app.task()
def remove_stale_contenttypes():
    call_command('remove_stale_contenttypes')

@app.task()
def delete_expired_uploads():
    call_command('delete_expired_uploads')
