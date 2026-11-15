"""Alertas configurables de organilab sobre ``djgentelella.alerts``.

djgentelella pone el núcleo: el registro de procesos y disparadores (en código), los
modelos abstractos, ``fire_alert`` con ``dedupe_key``, ``resolve_alert`` y los canales.
Este módulo es la fachada de organilab y suma lo propio del proyecto:

* **Destinatarios** (``rule_recipients``): el responsable que indique el proceso, si la
  regla lo pide, más los usuarios con los roles de la regla en su organización.
* **Canales:**
  * ``email`` sale por ``send_process_email`` y respeta la ``NotificationSetting`` de la
    organización.
  * ``notification`` (la campana) avisa solo las críticas.
  * ``pending_task`` crea la tarea pendiente y la cierra cuando la alerta se resuelve.

Una app registra su proceso en ``AppConfig.ready``::

    register_alert_process(
        "ambiental.consumption", label=_("Atypical consumption"),
        evaluator="ambiental.alerts.evaluate_rule",
        triggers=(TRIGGER_PERCENT, TRIGGER_ABSOLUTE, TRIGGER_MISSING),
        permission="ambiental.add_measurementpoint",
        notification_code="ambiental-consumption-alert",
    )
"""
import logging

from django.contrib.auth import get_user_model
from djgentelella.alerts import (  # noqa: F401  (API pública de la fachada)
    TRIGGER_ABSOLUTE,
    TRIGGER_DUE,
    TRIGGER_MISSING,
    TRIGGER_PERCENT,
    AlertChannel,
    EmailChannel,
    NotificationChannel,
    due_status,
    fire_due_alert,
    get_process,
    get_trigger,
    processes_for,
    register_alert_process,
    register_channel,
    resolve_alert,
    run_alert_rules,
    trigger_choices,
    validate_threshold,
)
from djgentelella.alerts import fire_alert as core_fire_alert
from djgentelella.alerts.triggers import TRIGGERS

logger = logging.getLogger("organilab")


def threshold_fields():
    """``{campo: (disparador, ThresholdField)}`` de todos los disparadores registrados."""
    return {
        name: (code, field)
        for code, trigger in TRIGGERS.items()
        for name, field in trigger.threshold_fields.items()
    }


def threshold_display(rule):
    """Texto del umbral de la regla para las listas: ``Etiqueta: valor, ...``."""
    try:
        trigger = get_trigger(rule.trigger)
    except Exception:
        return ""
    return ", ".join(
        "%s: %s" % (field.label, (rule.threshold or {}).get(name, ""))
        for name, field in trigger.threshold_fields.items()
        if (rule.threshold or {}).get(name, "") != ""
    )


def threshold_value(rule, name=None):
    return rule.threshold_value(name)


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


def fire_alert(rule, message, obj=None, responsible_users=(), context=None, link="",
               recipient_filter=None, dedupe_key="", renotify_after=None):
    """Registra el disparo de la regla y avisa por los canales del proceso.

    Con ``dedupe_key``, mientras haya un evento abierto con esa clave no se crea otro.
    """
    users = rule_recipients(rule, responsible_users, recipient_filter)
    return core_fire_alert(
        rule, message, obj, dedupe_key=dedupe_key, recipients=users, context=context,
        link=link, renotify_after=renotify_after,
    )


# --- Canales de organilab ----------------------------------------------------------

def send_organization_email(event, code, emails, context):
    from presentation.notifications import send_process_email

    send_process_email(event.rule.organization, code, context, emails)


class PendingTaskChannel(AlertChannel):
    """Tarea pendiente por destinatario (si la regla lo pide), cerrada al resolver."""

    name = "pending_task"

    def applies(self, event):
        return event.rule.create_task

    def send(self, event, users, context):
        from django.contrib.contenttypes.models import ContentType

        from pending_tasks.models import PendingTaskManager
        from pending_tasks.utils import create_pending_task

        rule = event.rule
        if rule.created_by is None:
            logger.warning("La regla de alerta %s no tiene creador: no se crea tarea", rule.pk)
            return
        roles = list(rule.notify_roles.all())
        profiles = [getattr(user, "profile", None) for user in users] or [None]
        content_type = ContentType.objects.get_for_model(event)
        for profile in profiles:
            task = create_pending_task(
                rule.created_by, str(event.message)[:255], roles, description=str(event.message),
                profile=profile, link=event.link, notify=True,
            )
            PendingTaskManager.objects.create(content_type=content_type, object_id=event.pk, task=task)

    def on_resolve(self, event, resolution=None, user=None):
        from django.contrib.contenttypes.models import ContentType

        from pending_tasks.models import PendingTask

        PendingTask.objects.filter(
            pendingtaskmanager__content_type=ContentType.objects.get_for_model(event),
            pendingtaskmanager__object_id=event.pk,
        ).exclude(status=PendingTask.FINISHED).update(status=PendingTask.FINISHED)


def register_organilab_channels():
    register_channel(EmailChannel(sender=send_organization_email))
    register_channel(NotificationChannel(levels=["critical"]))
    register_channel(PendingTaskChannel())


register_organilab_channels()
