"""
Created on 10 mar. 2018
@author: luisza
"""

from async_notifications.utils import send_email_from_template
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.translation import gettext_lazy as _
import logging

from auth_and_perms.models import Profile
from django.contrib.admin.models import ADDITION
from laboratory.models import Object
from laboratory.utils import organilab_logentry
from pending_tasks.models import PendingTask
from sga.models import SubstanceCharacteristics
from sga.substance_codes import build_substance_code

logger = logging.getLogger("organilab")


def _send(code, email, subject, body):
    try:
        send_email_from_template(
            code,
            email,
            context={"subject": subject, "body": body},
            enqueued=False,
            user=None,
            upfile=None,
        )
    except Exception as e:
        logger.error("Error sending new substace email", exc_info=e)


def notify_request_created(instance, user, url=None):
    subject = _("New substance request: %(name)s") % {
        "name": instance["name"],
    }
    body = _(
        "Hi,\n\n"
        "A new substance request has been submitted and requires your review.\n\n"
        "Name: %(name)s\n"
        "Requested by: %(user)s\n\n"
        "Please log in to review this request.\n\n"
        "Thanks,\nOrganilab system"
    ) % {
        "name": instance["name"],
        "user": user.get_full_name() or user.username,
    }
    emails = list(
        Group.objects.filter(name="RegisterOrganization")
        .values_list("user__email", "user__pk")
        .exclude(user__email="")
        .distinct()
    )
    for email, pk in emails:
        try:
            profile = Profile.objects.get(user__pk=pk)
        except Profile.DoesNotExist:
            continue
        PendingTask.objects.create(
            name="New Substance Request", description=body, profile=profile, link=url
        )
        _send("lab_or_org_request_created", email, subject, body)


def assign_substance_codes(instance, obj=None):
    """Emite el código de cada pareja sustancia-laboratorio de esta solicitud.

    Es idempotente: el código no lleva consecutivo, así que reaprobar devuelve el
    mismo valor y no consume numeración. Si a un laboratorio o a la organización
    le falta la sigla no se emite nada y queda constancia en el log; aprobar no
    debe fallar por eso, igual que subir una ficha no falla si la extracción sí.
    """
    from sga.models import SubstanceLaboratory

    organization = instance.organization
    emitidos = []
    sin_sigla = []

    for enlace in SubstanceLaboratory.objects.filter(
        substance=instance
    ).select_related("laboratory"):
        code = build_substance_code(enlace.laboratory, organization, instance)
        if not code:
            sin_sigla.append(enlace.laboratory_id)
            continue
        if enlace.code != code:
            enlace.code = code
            enlace.save(update_fields=["code"])
        emitidos.append(code)

    if sin_sigla:
        logger.warning(
            "Sustancia %s: sin código para los laboratorios %s porque falta la "
            "sigla del laboratorio o de la organización.",
            instance.pk,
            sin_sigla,
        )

    # El objeto de inventario es único y de la organización, así que solo cabe un
    # código: se toma el del primer laboratorio como referencia visible en el
    # listado de reactivos. El código completo por laboratorio vive en su fila.
    if obj is not None and emitidos and not obj.code:
        obj.code = emitidos[0]
        obj.save(update_fields=["code"])

    return emitidos


def create_object_notification(instance, user=None):
    """Da de alta el reactivo aprobado y lo registra en cada laboratorio.

    El objeto de inventario es uno solo y pertenece a la organización —todos sus
    laboratorios lo ven igual—, así que los laboratorios de la solicitud no dan
    visibilidad: aportan la traza y, sobre todo, el código. Cada uno recibe en su
    bitácora el alta del reactivo que pidió y su propio `EQ-LAB-ORG-000031`.
    """
    suscharobj = SubstanceCharacteristics.objects.filter(substance=instance).first()
    if suscharobj is None:
        logger.error(
            "No se puede crear el objeto de inventario: la sustancia %s no tiene "
            "características asociadas.",
            instance.pk,
        )
        return None

    with transaction.atomic():
        obj = Object.objects.create(
            created_by=instance.created_by,
            organization=instance.organization.root,
            name=instance.comercial_name,
            type=Object.REACTIVE,
            has_threshold=suscharobj.has_threshold,
            threshold=suscharobj.threshold,
            is_dangerous=suscharobj.is_dangerous,
            is_pure=suscharobj.is_pure,
            description=instance.description,
        )
        obj.features.add(*instance.features.all())
        suscharobj.object_related = obj
        suscharobj.save(update_fields=["object_related"])

        assign_substance_codes(instance, obj)

        # `created_by` es anulable, así que el usuario que aprueba es el origen
        # fiable; el otro queda de respaldo.
        actor = user or instance.created_by
        laboratories = list(instance.laboratories.all())
        if actor and laboratories:
            # organilab_logentry acepta la lista y crea un LabOrgLogEntry por
            # laboratorio, que es lo que hace visible el alta en cada bitácora.
            organilab_logentry(
                actor,
                obj,
                ADDITION,
                "object",
                changed_data=["name", "type", "organization"],
                change_message=_("Approved substance '%(name)s' added to inventory")
                % {"name": instance.comercial_name},
                relobj=laboratories,
            )
        elif not laboratories:
            logger.warning(
                "La sustancia %s se aprobó sin laboratorios: el alta del objeto "
                "%s no queda registrada en ninguna bitácora.",
                instance.pk,
                obj.pk,
            )
    return obj
