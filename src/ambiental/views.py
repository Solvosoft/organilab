from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from ambiental.forms import MeasurementPointForm
from auth_and_perms.organization_utils import user_is_allowed_on_organization


@login_required
@permission_required("ambiental.view_measurementpoint", raise_exception=True)
def measurementpoint_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        "org_pk": org_pk,
        "form_create": MeasurementPointForm(prefix="create"),
        "form_update": MeasurementPointForm(prefix="update"),
    }
    return render(request, "ambiental/measurementpoint_list.html", context=context)
