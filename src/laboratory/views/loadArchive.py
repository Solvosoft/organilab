import openpyxl
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.response import Response

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from laboratory.api.serializers import LoadArchiveSerializer
from laboratory.forms import LoadArchiveForm
from laboratory.models import OrganizationStructure, Laboratory
from datetime import datetime

HEADER_ROW = 7
DATA_START_ROW = 8

COLUMNS = {
    "nombre_producto": 1,          # A
    "numero_cas": 2,               # B
    "formula_quimica": 3,          # C
    "estado": 4,                   # D
    "cantidad": 5,                 # E
    "unidades_cantidad": 6,        # F
    "capacidad_envase": 7,         # G
    "unidades_capacidad": 8,       # H
    "numero_envases": 9,           # I
    "material_contenedor": 10,     # J
    "cantidad_maxima_anual": 11,   # K
    "unidades_cantidad_maxima": 12,# L
    "fecha_caducidad": 13,         # M
}


def read_xlsm_data(uploaded_file):
    wb = openpyxl.load_workbook(uploaded_file, keep_vba=True)
    ws = wb['Formato de Iventario']

    records = []
    for row in ws.iter_rows(min_row=DATA_START_ROW, max_row=ws.max_row,
                            values_only=True):
        nombre = row[COLUMNS["nombre_producto"] - 1]

        if not nombre:
            continue

        estado = row[COLUMNS["estado"] - 1]
        unidades = row[COLUMNS["unidades_cantidad"] - 1]
        fecha = row[COLUMNS["fecha_caducidad"] - 1]
        numero_envases = row[COLUMNS["numero_envases"] - 1] or 1

        record = {
            "nombre_producto": nombre,
            "numero_cas": row[COLUMNS["numero_cas"] - 1],
            "formula_quimica": row[COLUMNS["formula_quimica"] - 1],
            "estado": None if estado == "Seleccione" else estado,
            "cantidad": row[COLUMNS["cantidad"] - 1],
            "unidades_cantidad": None if unidades == "Seleccione" else unidades,
            "capacidad_envase": row[COLUMNS["capacidad_envase"] - 1],
            "unidades_capacidad": row[COLUMNS["unidades_capacidad"] - 1],
            "material_contenedor": row[COLUMNS["material_contenedor"] - 1],
            "cantidad_maxima_anual": row[COLUMNS["cantidad_maxima_anual"] - 1],
            "unidades_cantidad_maxima": row[COLUMNS["unidades_cantidad_maxima"] - 1],
            "fecha_caducidad": fecha.date().isoformat() if isinstance(fecha, datetime) else fecha,
        }

        for _ in range(int(numero_envases)):
            records.append(record.copy())

    return records


@login_required
@permission_required("laboratory.add_shelfobject", raise_exception=True)
def load_archive(request, org_pk, lab_pk):
    org = get_object_or_404(
        OrganizationStructure, pk=org_pk
    )
    lab = get_object_or_404(
        Laboratory, pk=lab_pk
    )
    user_is_allowed_on_organization(request.user, org)
    organization_can_change_laboratory(lab, org)
    if request.method == "POST":
        data = {
            "file": request.POST.get("create-file"),
            "lab_room": request.POST.get("create-lab_room"),
            "furniture": request.POST.get("create-furniture"),
            "shelf": request.POST.get("create-shelf"),
        }
        serializer = LoadArchiveSerializer(data=data)
        if not serializer.is_valid():
            return render(request, "laboratory/load_archive/load_archive.html", {
                "org_pk": org_pk,
                "lab_pk": lab_pk,
                "laboratory": lab_pk,
                "create_form": LoadArchiveForm(prefix="create"),
                "errors": serializer.errors,
            })
        uploaded_file = serializer.validated_data["file"]
        data = read_xlsm_data(uploaded_file)
        result = {
            "lab_room": serializer.validated_data["lab_room"],
            "furniture": serializer.validated_data["furniture"],
            "shelf": serializer.validated_data["shelf"],
            "data": data,
        }
        return Response({"result": result}, status=status.HTTP_200_OK)
    return render(
        request, "laboratory/load_archive/load_archive.html",
        context={
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "laboratory": lab_pk,
            "create_form": LoadArchiveForm(prefix="create"),
        }
    )
