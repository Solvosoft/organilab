from __future__ import absolute_import, unicode_literals

import importlib
from datetime import date, datetime, timedelta
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext as _

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
            risk.buildings.using(settings.READONLY_DATABASE)
            .all()
            .values_list("laboratories__pk", flat=True)
        )
        create_estableshment_logs_data(risk, day, labs)

    for org in OrganizationStructure.objects.all():
        try:
            labs = list(set(org.get_my_laboratories))
            create_estableshment_logs_data(org, day, labs)
        except OrganizationStructure.DoesNotExist:
            continue


@app.task
def send_iper_update_reminders():
    """Crea una tarea pendiente al responsable de cada laboratorio cuyo IPER esté
    por vencer (según IPERConfig.period_months/reminder_days_before)."""
    from pending_tasks.utils import create_pending_task
    from risk_management.models import IPERAssessment
    from risk_management.models_utils import get_iper_config

    today = now().date()
    seen_labs = set()
    queryset = (
        IPERAssessment.objects.exclude(status=IPERAssessment.OBSOLETE)
        .select_related("laboratory", "responsible", "organization")
        .order_by("-version")
    )
    for assessment in queryset:
        lab = assessment.laboratory
        if lab.pk in seen_labs:
            continue
        seen_labs.add(lab.pk)
        if assessment.due_date is None:
            continue
        cfg = get_iper_config(assessment.organization, lab)
        reminder_days = cfg.reminder_days_before if cfg else 30
        if assessment.due_date - timedelta(days=reminder_days) > today:
            continue
        responsible = lab.responsible
        if responsible is None or getattr(responsible, "profile", None) is None:
            continue
        create_pending_task(
            responsible,
            _("Update the IPER risk assessment"),
            [],
            description=_("The IPER for laboratory %(lab)s is due on %(date)s.")
            % {"lab": lab.name, "date": assessment.due_date},
            profile=responsible.profile,
            link=reverse(
                "riskmanagement:iper_list",
                kwargs={"org_pk": assessment.organization_id},
            ),
            notify=True,
        )
