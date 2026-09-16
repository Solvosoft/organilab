from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from ambiental.forms import BuildingFilterForm, ConsumptionRecordForm, MeasurementPointForm
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure


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


@login_required
@permission_required("ambiental.view_consumptionrecord", raise_exception=True)
def consumptionrecord_list(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    context = {
        "org_pk": org_pk,
        "building_form": BuildingFilterForm(),
        "form_create": ConsumptionRecordForm(prefix="create", organization=organization),
        "form_update": ConsumptionRecordForm(prefix="update", organization=organization),
    }
    return render(request, "ambiental/consumptionrecord_list.html", context=context)
