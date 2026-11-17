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
            "shelfobject__object", "shelfobject__in_where_laboratory__responsible",
            "shelfobject__shelfobjectequipmentcharacteristics__custodian__user",
        )
        .prefetch_related("responsible__user")
    )


def plan_responsibles(plan):
    """Responsables del programa, custodio del equipo y responsable del laboratorio."""
    users = []
    users.extend(profile.user for profile in plan.responsible.all())
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
    return " ".join(part for part in (code, shelfobject.object.name) if part)


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


# --- Reglas por defecto ----------------------------------------------------------------

def default_rules():
    """``{proceso: datos de la regla}`` que se crea sola la primera vez que se usa."""
    from laboratory.equipment import control
    from presentation.alerts import TRIGGER_DUE

    return {
        PROCESS: {
            "name": _("Equipment activities due"),
            "trigger": TRIGGER_DUE,
            "threshold": {"days_before": 30, "overdue_repeat_days": 7},
        },
        control.PROCESS: {
            "name": _("Equipment control charts out of control"),
            "trigger": control.TRIGGER_OUT_OF_CONTROL,
            "threshold": {},
        },
    }


def ensure_default_rule(process, organization, user=None):
    """Crea la regla del proceso si ni la organización ni sus ancestros tienen una.

    Sin regla nadie recibe los avisos, y pedir que alguien la configure antes de
    registrar el primer programa hacía que las alertas no salieran nunca. Una regla
    desactivada cuenta: quien la apagó no la quiere de vuelta. Sin ``user`` la regla
    avisa por correo pero no crea tareas pendientes (necesitan un creador).
    """
    from presentation.models import AlertRule

    if organization is None:
        return None
    if AlertRule.objects.filter(process=process, organization__in=organization.ancestors(include_self=True)).exists():
        return None
    return AlertRule.objects.create(
        organization=organization, process=process, created_by=user,
        notify_responsible=True, create_task=True, **default_rules()[process],
    )


def ensure_rules_for_existing_plans():
    """Reglas por defecto para las organizaciones que ya tenían programas sin regla."""
    from laboratory.models import EquipmentActivityPlan

    created = []
    plans = (
        EquipmentActivityPlan.objects.filter(is_active=True, shelfobject__in_where_laboratory__isnull=False)
        .select_related("shelfobject__in_where_laboratory__organization", "created_by")
        .order_by("shelfobject__in_where_laboratory__organization_id", "pk")
        .distinct("shelfobject__in_where_laboratory__organization_id")
    )
    for plan in plans:
        rule = ensure_default_rule(PROCESS, plan.shelfobject.in_where_laboratory.organization, plan.created_by)
        if rule is not None:
            created.append(rule)
    return created
