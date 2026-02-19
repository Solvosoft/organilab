"""
Created on /8/2016

@author: natalia
"""

from laboratory.forms import ObjectFeaturesForm
from django.contrib.auth.decorators import permission_required
from laboratory.models import ObjectFeatures, Laboratory
from django.shortcuts import render, get_object_or_404
from auth_and_perms.organization_utils import user_is_allowed_on_organization


@permission_required("laboratory.view_objectfeatures")
def objectfeatures_view(request, org_pk=0, lab_pk=0):
    user_is_allowed_on_organization(request.user, org_pk)

    return render(
        request,
        "laboratory/objectfeatures_list.html",
        context={
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "laboratory": lab_pk,
            "form_create": ObjectFeaturesForm(prefix="create", render_type="as_p"),
            "form_update": ObjectFeaturesForm(prefix="update", render_type="as_p"),
        },
    )
