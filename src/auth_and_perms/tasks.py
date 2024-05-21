from __future__ import absolute_import, unicode_literals

import importlib

from django.conf import settings
from django.db.models import ExpressionWrapper, Q, F, BooleanField

from auth_and_perms.models import DeleteUserList

app = importlib.import_module(settings.CELERY_MODULE).app

@app.task()
def update_delete_users_list():
    recent_last_login = ExpressionWrapper(Q(last_login__gte=F('creation_date')),
                                          output_field=BooleanField())
    DeleteUserList.objects.annotate(equal=recent_last_login).filter(equal=True).delete()
