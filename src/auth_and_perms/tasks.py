from __future__ import absolute_import, unicode_literals

import importlib

from django.conf import settings
from django.db.models import ExpressionWrapper, Q, F, BooleanField

from auth_and_perms.models import DeleteUserList
from auth_and_perms.users import warning_notification_delete_user

app = importlib.import_module(settings.CELERY_MODULE).app

@app.task()
def update_delete_users_list():
    recent_last_login = ExpressionWrapper(Q(last_login__gte=F('creation_date')),
                                          output_field=BooleanField())
    DeleteUserList.objects.annotate(user_recent_last_login=recent_last_login).filter(
        user_recent_last_login=True).delete()

@app.task()
def send_notification_warning_delete_user():
    warning_notification_delete_user(8)
    warning_notification_delete_user(1)

