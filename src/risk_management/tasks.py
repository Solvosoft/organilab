from __future__ import absolute_import, unicode_literals

import importlib
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils.timezone import now

from laboratory.models import OrganizationStructure
from risk_management.models import RiskZone
from risk_management.utils_risk import (
    create_estableshment_logs_data,
)

app = importlib.import_module(settings.CELERY_MODULE).app


@app.task
def create_establishment_reports():
    day = now().date() - timedelta(days=1)
    for risk in RiskZone.objects.all():
        labs = list(
            risk.laboratories.using(settings.READONLY_DATABASE)
            .all()
            .values_list("pk", flat=True)
        )
        create_estableshment_logs_data(risk, day, labs)
    for org in OrganizationStructure.objects.all():
        labs = list(
            org.laboratory_set.using(settings.READONLY_DATABASE)
            .all()
            .values_list("pk", flat=True)
        )
        create_estableshment_logs_data(org, day, labs)
