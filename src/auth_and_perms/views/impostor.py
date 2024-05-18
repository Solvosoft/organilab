from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import ImpostorLog
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from auth_and_perms.utils import get_ip_address
from laboratory.models import OrganizationStructure, UserOrganization


@login_required
@permission_required("auth_and_perms.change_impostorlog")
def add_user_impostor(request, org_pk, pk):
    response= redirect(reverse('index'))
    User = get_user_model()
    ipaddress = get_ip_address(request)
    imposted_as=get_object_or_404(User, pk=pk)

    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE),
        pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)

    user_in_org=UserOrganization.objects.filter(organization=org_pk,user=imposted_as).exists()
    if user_in_org:
        if request.user.pk != imposted_as.pk:
            exist_instance=ImpostorLog.objects.filter(
                impostor=request.user,
                imposted_as=imposted_as,
                impostor_ip=ipaddress,
                active=True
                ).exists()
            if not exist_instance:
                instance=ImpostorLog(
                    impostor=request.user,
                    imposted_as=imposted_as,
                    impostor_ip=ipaddress)
                instance.save()
                request.session['impostor']=pk
                response.set_cookie('impostor_token', str(instance.token))
            else:
                messages.error(request, mark_safe(_('You have active impostor session <a href="%(reverseurl)s?all=1">Finish it</a>')%{
                    'reverseurl': reverse('auth_and_perms:remove_impostor')
                }))
        else:
            messages.error(request, _("Request User is the same as current user"))
    else:
        messages.error(request, _("User not in organization"))
    return response

@login_required
def remove_impostor(request):
    delall = request.GET.get('all', None)
    if delall:
        if hasattr(request, 'impostor_info'):
            ImpostorLog.objects.filter(
                impostor=request.impostor_info.impostor,
                active=True).update(active=False, logged_out=now())
        else:
            ImpostorLog.objects.filter(
                impostor=request.user,
                active=True).update(active=False, logged_out=now())
    else:
        ipaddress = get_ip_address(request)
        ImpostorLog.objects.filter(
            imposted_as=request.user,
            impostor_ip=ipaddress).update(active=False, logged_out=now())
    impostor = request.session.get('impostor', None)
    if impostor:
        del request.session['impostor']
    response = redirect(reverse('index'))
    response.set_cookie('impostor_token', '')
    return response
