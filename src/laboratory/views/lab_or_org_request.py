from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.forms import LabOrOrgRequestForm, LabOrOrgRequestFilterForm
from laboratory.models import OrganizationStructure


@login_required
@permission_required("laboratory.add_labororgrequest", raise_exception=True)
def lab_or_org_request_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    org = get_object_or_404(OrganizationStructure, pk=org_pk)
    return render(
        request,
        "laboratory/lab_or_org_request/list.html",
        context={
            "org_pk": org_pk,
            "org": org,
            "form_create": LabOrOrgRequestForm(
                org_pk=org_pk, prefix="create", render_type="as_grid"
            ),
            "form_update": LabOrOrgRequestForm(
                org_pk=org_pk, prefix="update", render_type="as_grid"
            ),
            "form_filter": LabOrOrgRequestFilterForm(
                prefix="filter", render_type="as_grid"
            ),
        },
    )


@login_required
@permission_required("laboratory.can_approve_labororgrequest", raise_exception=True)
def lab_or_org_request_review_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    org = get_object_or_404(OrganizationStructure, pk=org_pk)
    return render(
        request,
        "laboratory/lab_or_org_request/review.html",
        context={
            "org_pk": org_pk,
            "org": org,
            "form_filter": LabOrOrgRequestFilterForm(
                prefix="filter", render_type="as_grid"
            ),
        },
    )
