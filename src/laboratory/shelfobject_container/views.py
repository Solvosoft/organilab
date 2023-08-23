from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from .forms import ShelfFilterForm
from ..models import OrganizationStructure, Laboratory
from ..utils import check_user_access_kwargs_org_lab


def show_shelf_container(request, org_pk, lab_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    laboratory = get_object_or_404(
        Laboratory.objects.using(settings.READONLY_DATABASE),
        pk=lab_pk)
    organization_can_change_laboratory(laboratory, organization,
                                       raise_exec=True)

    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404()

    form = ShelfFilterForm(lab_pk, request.GET)
    if not form.is_valid():
        raise Http404(form.errors['shelf'])
    return render(request, 'laboratory/containers/container_list.html',
                  context={
                      'org_pk': org_pk,
                      'laboratory': lab_pk,
                      'shelf': form.cleaned_data['shelf']
                  })
