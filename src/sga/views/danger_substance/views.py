from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from rest_framework.generics import get_object_or_404

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from sga.forms import DangerSubstanceForm


@permission_required("sga.view_dangersubstance")
def danger_substance_view(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE),
        pk=org_pk,
    )
    user_is_allowed_on_organization(request.user, organization)
    return render(
        request,
        "danger_substance/danger_substance.html",
        context={
            "form_create": DangerSubstanceForm(prefix="create"),
            "form_update": DangerSubstanceForm(prefix="update"),
            "org_pk": org_pk
        }
    )
