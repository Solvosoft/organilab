"""Importación de equipos desde Excel: subir, revisar fila por fila y crear.

Sigue el flujo de ``laboratory/views/loadArchive.py``: el archivo se lee, las filas se
guardan temporalmente (``TemporalUploadEquipment``) y una pantalla de revisión permite
corregir, descartar filas y elegir responsables antes de crear nada.
"""
import io

import openpyxl
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from auth_and_perms.models import Profile
from auth_and_perms.organization_utils import organization_can_change_laboratory, user_is_allowed_on_organization
from laboratory.equipment.import_forms import (
    EquipmentImportFileSerializer,
    EquipmentImportForm,
    EquipmentImportRowForm,
    row_initial,
)
from laboratory.equipment.import_service import EquipmentImporter, ProfileMatcher
from laboratory.equipment.importer import INVENTORY, PROGRAM, read_workbook
from laboratory.models import Laboratory, OrganizationStructure, TemporalUploadEquipment


TEMPLATE_HEADERS = (
    "Equipo", "Marca", "Modelo", "Serie", "N° Activo", "Codigo del laboratorio", "Responsable",
    "Verificacion", "Ubicación", "Placa",
)
TEMPLATE_EXAMPLE = (
    "Balanza granataria", "Senderpick", "KW-089", "S-12345", "N00123386", "LB-127", "XVR", "",
    "Mesa de balanzas", "",
)


def scope(request, org_pk, lab_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization, raise_exec=True)
    return organization, laboratory


def base_context(org_pk, lab_pk, **extra):
    return {"org_pk": org_pk, "lab_pk": lab_pk, "laboratory": lab_pk, **extra}


def mark_conflicts(formset, laboratory):
    """Marca las filas cuyo código ya es de un equipo con otro nombre en el laboratorio.

    El código identifica al equipo: importar esa fila completaría la ficha existente con
    datos de otro equipo. Se avisa en la revisión y la persona decide.
    """
    from laboratory.equipment.importer import normalize_label
    from laboratory.models import ShelfObjectEquipmentCharacteristics

    existing = {
        code.lower(): name
        for code, name in ShelfObjectEquipmentCharacteristics.objects.filter(
            shelfobject__in_where_laboratory=laboratory
        ).exclude(internal_code="").values_list("internal_code", "shelfobject__object__name")
    }
    elsewhere = {
        code.lower(): lab_name
        for code, lab_name in ShelfObjectEquipmentCharacteristics.objects.filter(
            shelfobject__in_where_laboratory__organization=laboratory.organization
        ).exclude(shelfobject__in_where_laboratory=laboratory).exclude(internal_code="")
        .values_list("internal_code", "shelfobject__in_where_laboratory__name")
    }
    for form in formset:
        code = str(form["internal_code"].value() or "").strip().lower()
        name = str(form["name"].value() or "")
        current = existing.get(code)
        form.existing_name = current if current and normalize_label(current) != normalize_label(name) else ""
        # El código es único en la organización: en otro laboratorio la fila crearía un duplicado.
        form.other_laboratory = "" if current else elsewhere.get(code, "")


@login_required
@permission_required(["laboratory.add_shelfobject", "laboratory.add_object"], raise_exception=True)
def equipment_import(request, org_pk, lab_pk):
    organization, laboratory = scope(request, org_pk, lab_pk)
    form = EquipmentImportForm(request.POST or None, laboratory=laboratory, prefix="import")
    if request.method == "POST":
        upload = EquipmentImportFileSerializer(data={"file": request.POST.get("import-file")})
        if not upload.is_valid():
            form.is_valid()
            for message in upload.errors.get("file", []):
                form.add_error("file", message)
        elif form.is_valid():
            sheet, rows = read_workbook(
                upload.validated_data["file"], form.cleaned_data["kind"], form.cleaned_data["sheet"] or None
            )
            if not rows:
                form.add_error("file", _("No sheet with the selected format and equipment rows was found."))
            else:
                temp = TemporalUploadEquipment.objects.create(
                    laboratory=laboratory, shelf=form.cleaned_data["shelf"], kind=form.cleaned_data["kind"],
                    sheet=sheet, data=rows, created_by=request.user,
                )
                return redirect("laboratory:equipment_import_review", org_pk=org_pk, lab_pk=lab_pk, key=temp.key)
    return render(request, "laboratory/equipment/import.html", base_context(org_pk, lab_pk, form=form))


@login_required
@permission_required(["laboratory.add_shelfobject", "laboratory.add_object"], raise_exception=True)
def equipment_import_review(request, org_pk, lab_pk, key):
    organization, laboratory = scope(request, org_pk, lab_pk)
    temp = get_object_or_404(TemporalUploadEquipment, key=key, laboratory=laboratory)
    profiles = Profile.objects.filter(user__in=organization.users.all()).select_related("user")
    RowFormSet = formset_factory(EquipmentImportRowForm, extra=0)
    if request.method == "POST":
        formset = RowFormSet(request.POST, form_kwargs={"profiles": profiles})
        if formset.is_valid():
            importer = EquipmentImporter(organization, laboratory, temp.shelf, request.user, request)
            summary = importer.import_rows([form.as_row() for form in formset if form.cleaned_data.get("include")])
            temp.delete()
            messages.success(
                request,
                _("Import finished: %(created)s equipment created, %(updated)s updated, %(calibrations)s "
                  "calibrations, %(maintenances)s maintenances and %(plans)s programs registered.") % summary,
            )
            return redirect("laboratory:equipment_list", org_pk=org_pk, lab_pk=lab_pk)
    else:
        matcher = ProfileMatcher(organization)
        formset = RowFormSet(
            initial=[row_initial(row, matcher) for row in temp.data], form_kwargs={"profiles": profiles}
        )
    mark_conflicts(formset, laboratory)
    visible = EquipmentImportRowForm.VISIBLE_PROGRAM if temp.kind == PROGRAM else EquipmentImportRowForm.VISIBLE_INVENTORY
    return render(
        request,
        "laboratory/equipment/import_review.html",
        base_context(org_pk, lab_pk, formset=formset, temp=temp, visible=visible,
                     headers=[EquipmentImportRowForm.base_fields[name].label for name in visible
                              if name != "responsible"]),
    )


@login_required
@permission_required(["laboratory.add_shelfobject", "laboratory.add_object"], raise_exception=True)
def equipment_import_template(request, org_pk, lab_pk):
    scope(request, org_pk, lab_pk)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Inventario de equipos"
    sheet.append(TEMPLATE_HEADERS)
    sheet.append(TEMPLATE_EXAMPLE)
    buffer = io.BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="plantilla_equipos.xlsx"'
    return response


__all__ = ["equipment_import", "equipment_import_review", "equipment_import_template", "INVENTORY"]
