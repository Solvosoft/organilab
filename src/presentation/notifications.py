"""Correos de proceso administrables por organización.

``send_process_email`` es la puerta de salida de los correos que la organización puede
configurar: aplica el ``NotificationSetting`` más cercano (propio o de un ancestro) y
delega en ``djgentelella.async_notification``. Sin configuración, usa la plantilla
global tal cual.
"""
import logging

from django.template import Context, Template
from djgentelella.async_notification.models import EmailNotification, EmailTemplate
from djgentelella.async_notification.registry import get_all_contexts
from djgentelella.async_notification.sending import as_email_list, send_email_from_template

from presentation.parameters import organization_chain

logger = logging.getLogger("organilab")


def resolve_setting(organization, code):
    """``(setting, origin_org)`` del ancestro más cercano que configuró el código."""
    from presentation.models import NotificationSetting

    chain = organization_chain(organization)
    rows = {
        row.organization_id: row
        for row in NotificationSetting.objects.filter(code=code, organization__in=chain)
    }
    for org in chain:
        if org.pk in rows:
            return rows[org.pk], org
    return None, None


def registered_processes():
    """Los contextos de correo registrados con ``register_context``, por código."""
    return dict(sorted(get_all_contexts().items()))


def send_process_email(organization, code, context, recipients, user=None, enqueued=True):
    """Encola el correo del proceso para la organización; ``None`` si no se envía.

    No se envía si la organización (o un ancestro) lo apagó, si no hay destinatarios o
    si no existe plantilla ni texto propio: un proceso sin plantilla no debe tumbar la
    tarea que lo dispara.
    """
    recipients = as_email_list(recipients)
    if not recipients:
        return None
    setting, _origin = resolve_setting(organization, code)
    if setting is not None and not setting.is_active:
        return None

    template = EmailTemplate.objects.filter(code=code).first()
    has_override = setting is not None and (setting.override_subject or setting.override_message)
    if not has_override:
        if template is None:
            logger.warning("No hay plantilla de correo para el proceso %s", code)
            return None
        return send_email_from_template(code, recipients, context, enqueued=enqueued, user=user)

    subject = setting.override_subject or (template.subject if template else code)
    message = setting.override_message or (template.message if template else "")
    ctx = Context(context)
    return EmailNotification.objects.create(
        subject=Template(subject).render(ctx),
        message=Template(message).render(ctx),
        recipients=recipients,
        bcc=as_email_list(template.bcc) if template else [],
        cc=as_email_list(template.cc) if template else [],
        base_template=template.base_template if template else "",
        enqueued=enqueued,
        user=user,
    )
