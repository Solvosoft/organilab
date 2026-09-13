from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure


@login_required
def get_logentry_from_organization(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    return render(request, 'laboratory/logentry_list.html', context={'org_pk': org_pk})


get_logentry_from_organization.can_use_inactive_organization = True
