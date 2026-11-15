"""Listado de los equipos de un laboratorio con su estado y sus próximas fechas."""
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.urls import reverse

from laboratory.equipment.import_views import base_context, scope
from laboratory.models import ShelfObjectEquipmentCharacteristics


@login_required
@permission_required(["laboratory.view_shelfobject"], raise_exception=True)
def equipment_units(request, org_pk, lab_pk):
    scope(request, org_pk, lab_pk)
    return render(request, "laboratory/equipment/units.html", base_context(
        org_pk, lab_pk,
        list_url=reverse("laboratory:api-equipment-unit-list", kwargs={"org_pk": org_pk, "lab_pk": lab_pk}),
        statuses=ShelfObjectEquipmentCharacteristics.EQUIPMENT_STATUS,
    ))
