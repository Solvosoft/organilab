"""Alertas configurables: registro de procesos, validación de umbrales y disparo.

Una app que quiere alertas configurables registra su proceso en ``AppConfig.ready``::

    register_alert_process(
        "ambiental.consumption", label=_("Atypical consumption"),
        evaluator="ambiental.alerts.evaluate_rule",
        triggers=(TRIGGER_PERCENT, TRIGGER_ABSOLUTE, TRIGGER_MISSING),
        permission="ambiental.add_measurementpoint",
        notification_code="ambiental-consumption-alert",
    )

El evaluador recibe cada ``AlertRule`` activa del proceso y, cuando corresponde, llama
a ``fire_alert``, que deja el ``AlertEvent`` y avisa: correo por
``send_process_email``, tarea pendiente y, si la regla es crítica, notificación en la
campana.
"""
import logging
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("organilab")

KEY_ALERT_TRIGGER = "alert_trigger"
TRIGGER_PERCENT = "Variación porcentual"
TRIGGER_ABSOLUTE = "Umbral absoluto"
TRIGGER_MISSING = "Sin registro"
TRIGGERS = (TRIGGER_PERCENT, TRIGGER_ABSOLUTE, TRIGGER_MISSING)

#: disparador -> (campo del umbral, etiqueta, conversión)
THRESHOLD_FIELDS = {
    TRIGGER_PERCENT: ("percent", _("Percentage over the average"), Decimal),
    TRIGGER_ABSOLUTE: ("value", _("Maximum value"), Decimal),
    TRIGGER_MISSING: ("months", _("Months without records"), int),
}

ALERT_PROCESSES = {}


def register_alert_process(code, label, evaluator, triggers, permission=None, notification_code=""):
    ALERT_PROCESSES[code] = {
        "code": code,
        "label": label,
        "evaluator": evaluator,
        "triggers": tuple(triggers),
        "permission": permission,
        "notification_code": notification_code,
    }


def seed_alert_triggers(Catalog):
    for description in TRIGGERS:
        Catalog.objects.get_or_create(key=KEY_ALERT_TRIGGER, description=description)


def processes_for(user):
    """Los procesos cuyas reglas puede administrar el usuario."""
    return {
        code: info for code, info in ALERT_PROCESSES.items()
        if not info["permission"] or user.has_perm(info["permission"])
    }


def validate_threshold(trigger_description, raw_value):
    """``{campo: valor}`` del umbral, o ``ValueError`` con el motivo."""
    if trigger_description not in THRESHOLD_FIELDS:
        raise ValueError(_("Unknown trigger."))
    field, _label, convert = THRESHOLD_FIELDS[trigger_description]
    try:
        value = convert(str(raw_value).strip())
    except (TypeError, ValueError, InvalidOperation):
        raise ValueError(_("Enter a number."))
    if value <= 0:
        raise ValueError(_("The threshold must be greater than zero."))
    return {field: str(value) if isinstance(value, Decimal) else value}


def threshold_value(rule):
    field, _label, convert = THRESHOLD_FIELDS[rule.trigger.description]
    return convert(rule.threshold[field])


def rule_recipients(rule, responsible_users=(), recipient_filter=None):
    """Responsables (si la regla lo pide) más los usuarios con los roles de la regla.

    ``recipient_filter`` (``user -> bool``) permite al proceso descartar a quien no debe
    enterarse, p. ej. a quien no ve el edificio de la alerta.
    """
    from auth_and_perms.models import ProfilePermission

    users = {user.pk: user for user in responsible_users if user is not None} if rule.notify_responsible else {}
    roles = list(rule.notify_roles.all())
    if roles:
        user_ids = ProfilePermission.objects.filter(
            organization=rule.organization, rol__in=roles, profile__isnull=False
        ).values_list("profile__user", flat=True)
        for user in get_user_model().objects.filter(pk__in=user_ids):
            users.setdefault(user.pk, user)
    recipients = list(users.values())
    if recipient_filter is not None:
        recipients = [user for user in recipients if recipient_filter(user)]
    return recipients


def fire_alert(rule, message, obj=None, responsible_users=(), context=None, link="", recipient_filter=None):
    """Registra el disparo de la regla y avisa a quien corresponda."""
    from django.contrib.contenttypes.models import ContentType

    from pending_tasks.utils import create_pending_task
    from presentation.models import AlertEvent, AlertRule
    from presentation.notifications import send_process_email
    from report.utils import create_notification

    users = rule_recipients(rule, responsible_users, recipient_filter)
    event = AlertEvent.objects.create(
        rule=rule,
        organization=rule.organization,
        content_type=ContentType.objects.get_for_model(obj) if obj is not None else None,
        object_id=obj.pk if obj is not None else None,
        message=message,
        level=rule.level,
        link=link,
        recipients=[user.get_username() for user in users],
    )

    notification_code = rule.notification_code or ALERT_PROCESSES.get(rule.process, {}).get("notification_code")
    if notification_code:
        email_context = dict(context or {})
        email_context.update({"message": message, "link": link, "rule": rule})
        send_process_email(
            rule.organization, notification_code, email_context,
            [user.email for user in users if user.email],
        )

    if rule.create_task:
        if rule.created_by is None:
            logger.warning("La regla de alerta %s no tiene creador: no se crea tarea", rule.pk)
        else:
            roles = list(rule.notify_roles.all())
            profiles = [getattr(user, "profile", None) for user in users] or [None]
            for profile in profiles:
                create_pending_task(
                    rule.created_by, str(message)[:255], roles, description=str(message),
                    profile=profile, link=link, notify=True,
                )

    if rule.level == AlertRule.CRITICAL:
        for user in users:
            create_notification(user, str(message), link)
    return event


def run_alert_rules(process_code, **kwargs):
    """Evalúa todas las reglas activas del proceso. Devuelve cuántas se evaluaron."""
    from presentation.models import AlertRule

    info = ALERT_PROCESSES.get(process_code)
    if info is None:
        return 0
    evaluator = import_string(info["evaluator"])
    rules = AlertRule.objects.filter(process=process_code, is_active=True).select_related(
        "trigger", "organization", "created_by"
    )
    total = 0
    for rule in rules:
        try:
            evaluator(rule, **kwargs)
        except Exception:
            # Una regla rota no puede frenar la evaluación de las demás organizaciones.
            logger.exception("Falló la evaluación de la regla de alerta %s", rule.pk)
        total += 1
    return total
