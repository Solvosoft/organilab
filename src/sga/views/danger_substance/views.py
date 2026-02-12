from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from sga.forms import DangerSubstanceForm


@permission_required("sga.view_dangersubstance")
def danger_substance_view(request, org_pk):
    return render(
        request,
        "danger_substance/danger_substance.html",
        context={
            "form_create": DangerSubstanceForm(prefix="create"),
            "form_update": DangerSubstanceForm(prefix="update"),
            "org_pk": org_pk
        }
    )
