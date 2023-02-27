from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure


def get_roles_by_user(user):
    orgs = OrganizationStructure.os_manager.filter_user(user).values_list('pk', flat=True)
    return Rol.objects.filter(organizationstructure__in=orgs).distinct()


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