"""Alertas de actividades de equipo por vencer (ISO/IEC 17025 6.4.7, 6.4.10, 6.4.13).

Proceso ``laboratory.equipment_due``, disparador ``due`` de djgentelella.alerts:

* Cada programa activo (``EquipmentActivityPlan``) de un equipo que no esté dado de baja,
  en los laboratorios de la organización de la regla, avisa cuando su próxima fecha
  entra en los días de aviso **del programa** (``reminder_days_before``): cada equipo
  tiene su propio margen. Vencida, repite cada ``overdue_repeat_days`` de la regla.
* Un evento abierto por programa y fecha (``dedupe_key``): evaluar dos veces no duplica.
* Registrar la actividad (calibración, verificación, mantenimiento) mueve la fecha y
  resuelve la alerta con el registro como evidencia (``resolve_activity_alerts``).
"""
import datetime

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext as _

from presentation.alerts import due_status, fire_alert, resolve_alert

PROCESS = "laboratory.equipment_due"
NOTIFICATION_CODE = "equipment-activity-due"

#: actividad del programa -> pestaña de la ficha del equipo donde se registra
ACTIVITY_TAB = {
    "calibration": "calibrate",
    "verification": "verification",
    "preventive_maintenance": "maintenance",
    "cleaning": "maintenance",
    "other": "maintenance",
}


def active_plans(organization):
    from laboratory.models import EquipmentActivityPlan, ShelfObjectEquipmentCharacteristics

    organizations = organization.descendants(include_self=True)
    return (
        EquipmentActivityPlan.objects.filter(
            is_active=True,
            shelfobject__in_where_laboratory__organization__in=organizations,
            shelfobject__marked_as_discard=False,
        )
        .exclude(
            shelfobject__shelfobjectequipmentcharacteristics__equipment_status=(
                ShelfObjectEquipmentCharacteristics.DECOMMISSIONED
            )
        )
        .select_related(
            "responsible__user", "shelfobject__object", "shelfobject__in_where_laboratory__responsible",
            "shelfobject__shelfobjectequipmentcharacteristics__custodian__user",
        )
    )


def plan_responsibles(plan):
    """Responsable del programa, custodio del equipo y responsable del laboratorio."""
    users = []
    if plan.responsible_id:
        users.append(plan.responsible.user)
    characteristics = getattr(plan.shelfobject, "shelfobjectequipmentcharacteristics", None)
    if characteristics is not None and characteristics.custodian_id:
        users.append(characteristics.custodian.user)
    laboratory = plan.shelfobject.in_where_laboratory
    if laboratory is not None and laboratory.responsible_id:
        users.append(laboratory.responsible)
    return users


def equipment_name(shelfobject):
    characteristics = getattr(shelfobject, "shelfobjectequipmentcharacteristics", None)
    code = characteristics.internal_code if characteristics is not None else ""
    return " ".join(part for part in (code, str(shelfobject.object)) if part)


def plan_link(plan, organization):
    shelfobject = plan.shelfobject
    url = reverse(
        "laboratory:equipment_shelfobject_detail",
        kwargs={"org_pk": organization.pk, "lab_pk": shelfobject.in_where_laboratory_id, "pk": shelfobject.pk},
    )
    return "%s#pane-%s" % (url, ACTIVITY_TAB.get(plan.activity_kind, "plan"))


def plan_message(plan, status, next_due):
    params = {
        "activity": plan,
        "equipment": equipment_name(plan.shelfobject),
        "date": next_due.strftime("%d/%m/%Y"),
    }
    if status == "overdue":
        return _("%(activity)s of %(equipment)s is overdue since %(date)s.") % params
    return _("%(activity)s of %(equipment)s is due on %(date)s.") % params


def evaluate_rule(rule, today=None):
    """Dispara la regla para cada programa por vencer o vencido. Devuelve los eventos."""
    today = today or datetime.date.today()
    repeat = rule.threshold_value("overdue_repeat_days") or 0
    plan_type = None
    events = []
    for plan in active_plans(rule.organization):
        next_due = plan.next_due()
        status = due_status(next_due, today, plan.reminder_days_before)
        if status is None:
            continue
        plan_type = plan_type or ContentType.objects.get_for_model(plan)
        events.append(
            fire_alert(
                rule,
                plan_message(plan, status, next_due),
                obj=plan,
                responsible_users=plan_responsibles(plan),
                context={"plan": plan, "equipment": plan.shelfobject, "status": status, "next_due": next_due},
                link=plan_link(plan, rule.organization),
                dedupe_key="%s:%s:%s" % (plan_type.pk, plan.pk, next_due.isoformat()),
                renotify_after=datetime.timedelta(days=repeat) if status == "overdue" and repeat else None,
            )
        )
    return events


def resolve_activity_alerts(record, user=None):
    """Cierra las alertas abiertas de los programas que ``record`` acaba de cumplir.

    Un programa queda cumplido cuando ``record`` es su último registro: la próxima
    fecha ya se calcula desde él.
    """
    from laboratory.models import EquipmentActivityPlan

    closed = []
    for plan in EquipmentActivityPlan.objects.filter(shelfobject_id=record.shelfobject_id, is_active=True):
        last = plan.last_record()
        if last is not None and last._meta.model is record._meta.model and last.pk == record.pk:
            closed += resolve_alert(plan, resolution=record, user=user)
    return closed
