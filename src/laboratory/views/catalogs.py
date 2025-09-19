from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from laboratory.forms import InstrumentalFamilyForm, EquipmentTypeForm


@permission_required("laboratory.view_catalog")
def view_instrumental_family_list(request, org_pk, lab_pk):
    context = {
        "org_pk": org_pk,
        "lab_pk": lab_pk,
        "laboratory": lab_pk,
        "create_form": InstrumentalFamilyForm(prefix="create"),
        "update_form": InstrumentalFamilyForm(prefix="update"),
    }
    return render(request, "laboratory/instrumentalfamily/list.html", context=context)


@permission_required("laboratory.view_object")
def view_equipmenttype_list(request, org_pk, lab_pk):
    context = {
        "org_pk": org_pk,
        "lab_pk": lab_pk,
        "laboratory": lab_pk,
        "create_form": EquipmentTypeForm(prefix="create"),
        "update_form": EquipmentTypeForm(prefix="update"),
    }
    return render(request, "laboratory/equipmenttype/list.html", context=context)
