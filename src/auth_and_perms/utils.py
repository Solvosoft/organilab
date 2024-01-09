import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import OrganizationStructure


def get_roles_by_user(user):
    orgs = OrganizationStructure.os_manager.filter_user(user).values_list('pk', flat=True)
    return Rol.objects.filter(organizationstructure__in=orgs).distinct()


def get_rol_name(rol):
    org_str = ''
    for i, org in enumerate(rol.organizationstructure_set.all()):
        if i:
            org_str += " -- "
        org_str += org.name

    return f"{rol.pk} {rol.name} ({org_str})"


def get_roles_in_html(user, lab, org):
    profile = ProfilePermission.objects.filter(profile_id=user,
                                               content_type__app_label=lab._meta.app_label,
                                               content_type__model=lab._meta.model_name,
                                               object_id=lab.pk).first()
    roles = []
    if profile:
        for rol in profile.rol.filter(organizationstructure=org):
            rol_uuid=str(uuid.uuid4())
            datatext = """data-org="%d" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" """ % (
                org.pk, user, lab._meta.app_label, lab._meta.model_name, lab.pk
            )
            roles.append(
                """<span class="applyasrole" onclick="applyasrole('%s', %s)" id="rol_%s" style="color: %s;" title="%s" %s>%s</span>""" % (
                    rol_uuid, user, rol_uuid,
                    rol.color.replace('[', '').replace(']', '').replace("'", '').strip(),
                    get_rol_name(rol),
                    datatext,
                    rol.name[0]
                )
            )
        return " ".join(roles)


# Fixme: move to relevant place
def send_email(request, user):
    schema = request.scheme + "://"
    context = {
        'user': user,
        'domain': schema + request.get_host()
    }
    send_mail(subject="Nuevo usuario creado en la plataforma",
              message="Por favor use un visor de html",
              recipient_list=[user.email],
              from_email=settings.DEFAULT_FROM_EMAIL,
              html_message=render_to_string(
                  'gentelella/registration/new_user.html',
                  context=context
              )
              )
