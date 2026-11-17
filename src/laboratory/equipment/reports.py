"""Reportes de equipos (fase 2): programa anual PT-05 R-10 y hoja de vida del equipo.

El programa se exporta con los mismos encabezados del formato del laboratorio, que
``importer.read_program`` reconoce: el archivo exportado se puede editar en Excel y
volver a importar.
"""
import datetime
import io

import openpyxl
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext as _
from openpyxl.styles import Alignment, Font, PatternFill

from laboratory.equipment.import_views import scope
from laboratory.models import (
    EquipmentActivityPlan as Plan,
    Object,
    ShelfObject,
    ShelfObjectEquipmentCharacteristics as Characteristics,
)
from presentation.pdf import html_to_pdf

HEADER_TOP = 8
#: celda -> texto del encabezado (filas 8 a 12), como en el PT-05 R-10.
PROGRAM_HEADER = {
    "A8": "Magnitud", "B8": "Código", "C8": "Descripción", "D8": "Posición", "E8": "Estado del Equipo",
    "F8": "Datos del equipo", "F9": "Información General", "F10": "Marca", "G10": "Modelo", "H10": "Serie",
    "I10": "Versión del software y firmware", "J8": "Características metrológicas", "J9": "Unidad de medida",
    "K9": "Resolución", "L9": "Intervalo de indicaciones", "M8": "Responsables y uso",
    "M9": "Persona Responsable", "N9": "Usuarios activos", "O8": "Plan anual", "O9": "Calibración",
    "O10": "Fecha de Calibración", "P10": "Fecha de próxima calibración", "Q10": "Resultados",
    "R9": "Mantenimiento", "R10": "1", "R11": "Programado", "S11": "Ejecutado", "S12": "Tipo",
    "T12": "Inspección visual", "U12": "Limpieza", "V12": "Cambio de batería", "W12": "Pintura",
    "X12": "Engrasado", "Y12": "Incluye reporte de mantenimiento",
    "Z12": "Afecta los resultados de la última calibración",
    "AA12": "Detalles de cualquier daño, mal funcionamiento, modificación o reparación realizada",
}
PROGRAM_MERGES = (
    "A8:A12", "B8:B12", "C8:C12", "D8:D12", "E8:E12", "F8:I8", "F9:I9", "F10:F12", "G10:G12", "H10:H12",
    "I10:I12", "J8:L8", "J9:J12", "K9:K12", "L9:L12", "M8:N8", "M9:M12", "N9:N12", "O8:AA8", "O9:Q9",
    "O10:O12", "P10:P12", "Q10:Q12", "R9:AA9", "R10:AA10", "R11:R12", "S11:AA11",
)
CHECKLIST = ("Inspección visual", "Limpieza", "Cambio de batería", "Pintura", "Engrasado")
STATUS_TEXT = {
    Characteristics.IN_SERVICE: "Conforme",
    Characteristics.OUT_OF_SERVICE: "Fuera de servicio",
    Characteristics.IN_MAINTENANCE: "En mantenimiento",
    Characteristics.IN_CALIBRATION: "En calibración",
    Characteristics.DECOMMISSIONED: "Dado de baja",
}
CONFORMITY_TEXT = {"conforming": "Conforme", "non_conforming": "No conforme"}


def person(profile):
    if profile is None:
        return ""
    return profile.user.get_full_name() or profile.user.username


def equipment_queryset(laboratory, year):
    """Todo lo que lee cada fila, precargado: sin esto eran dos consultas por equipo."""
    from django.db.models import Prefetch

    from laboratory.models import ShelfObjectMaintenance

    return (
        ShelfObject.objects.filter(in_where_laboratory=laboratory, object__type=Object.EQUIPMENT)
        .select_related(
            "object", "shelfobjectequipmentcharacteristics__magnitude",
            "shelfobjectequipmentcharacteristics__custodian__user",
        )
        .prefetch_related(
            "equipmentactivityplan_set",
            "shelfobjectcalibrate_set",
            Prefetch(
                "shelfobjectmaintenance_set",
                queryset=ShelfObjectMaintenance.objects.filter(maintenance_date__year=year)
                .prefetch_related("activities"),
                to_attr="maintenances_of_year",
            ),
        )
        .order_by("shelfobjectequipmentcharacteristics__internal_code", "pk")
    )


def program_row(shelfobject, year):
    ch = getattr(shelfobject, "shelfobjectequipmentcharacteristics", None)
    calibrations = list(shelfobject.shelfobjectcalibrate_set.all())
    calibration = max(calibrations, key=lambda item: (item.calibration_date, item.pk)) if calibrations else None
    calibration_plan = next(
        (plan for plan in shelfobject.equipmentactivityplan_set.all() if plan.activity_kind == Plan.CALIBRATION
         and plan.is_active), None,
    )
    # La regla de EquipmentActivityPlan.next_due, con la calibración ya precargada.
    if calibration is None:
        next_calibration = calibration_plan.start_date if calibration_plan else None
    elif calibration.next_calibration_date or calibration_plan is None:
        next_calibration = calibration.next_calibration_date
    else:
        next_calibration = calibration.calibration_date + calibration_plan.interval()
    maintenances = getattr(shelfobject, "maintenances_of_year", None)
    if maintenances is None:
        maintenances = list(
            shelfobject.shelfobjectmaintenance_set.filter(maintenance_date__year=year).prefetch_related("activities")
        )
    maintenance = max(maintenances, key=lambda item: (item.maintenance_date, item.pk)) if maintenances else None
    maintenance_plan = next(
        (plan for plan in shelfobject.equipmentactivityplan_set.all()
         if plan.activity_kind == Plan.PREVENTIVE_MAINTENANCE and plan.is_active), None,
    )
    done = {activity.description for activity in maintenance.activities.all()} if maintenance else set()
    row = [
        str(ch.magnitude) if ch and ch.magnitude else "",
        ch.internal_code if ch else shelfobject.shelfobject_code or "",
        shelfobject.object.name,
        ch.physical_location if ch else "",
        STATUS_TEXT.get(ch.equipment_status, "") if ch else "",
        ch.brand if ch else "",
        ch.model if ch else "",
        ch.serial_number if ch else "",
        " / ".join(part for part in (ch.software_version, ch.firmware_version) if part) if ch else "",
        ch.measurement_unit if ch else "",
        ch.resolution if ch else "",
        ch.working_range if ch else "",
        person(ch.custodian) if ch else "",
        ch.access_restrictions if ch else "",
        calibration.calibration_date if calibration else "NA",
        next_calibration or "NA",
        CONFORMITY_TEXT.get(calibration.conformity, "") if calibration else "NA",
        year if maintenance_plan or maintenance else "NA",
        maintenance.get_maintenance_type_display() if maintenance else "",
    ]
    row += ["√" if name in done else ("x" if maintenance else "") for name in CHECKLIST]
    row += [
        ("si" if maintenance.report else "no") if maintenance else "",
        ("si" if maintenance.affects_calibration else "no") if maintenance else "",
        (maintenance.damage_details or "no") if maintenance else "",
    ]
    return row


def program_workbook(laboratory, year=None):
    year = year or timezone.localdate().year
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Formato PT-05 R-10"
    sheet["C1"] = str(laboratory)
    sheet["C3"] = _("Equipment program")
    sheet["C4"] = "PT-05 R-10 PROGRAMA DE EQUIPOS %s" % year
    bold, fill = Font(bold=True), PatternFill("solid", fgColor="DDEBF7")
    for cell, text in PROGRAM_HEADER.items():
        sheet[cell] = text
        sheet[cell].font, sheet[cell].fill = bold, fill
        sheet[cell].alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    for merged in PROGRAM_MERGES:
        sheet.merge_cells(merged)
    for index, shelfobject in enumerate(equipment_queryset(laboratory, year), start=HEADER_TOP + 5):
        for col, value in enumerate(program_row(shelfobject, year), start=1):
            cell = sheet.cell(index, col, value)
            if isinstance(value, datetime.date):
                cell.number_format = "DD/MM/YYYY"
    for col, width in zip("ABCDEFGHIJKLMNOPQ", (12, 10, 28, 18, 14, 14, 14, 16, 14, 12, 10, 16, 22, 22, 12, 12, 12)):
        sheet.column_dimensions[col].width = width
    return workbook


@login_required
@permission_required("laboratory.view_shelfobject", raise_exception=True)
def equipment_program_export(request, org_pk, lab_pk):
    _organization, laboratory = scope(request, org_pk, lab_pk)
    year = request.GET.get("year", "")
    workbook = program_workbook(laboratory, int(year) if year.isdigit() else None)
    buffer = io.BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="programa_equipos.xlsx"'
    return response


def life_record_context(shelfobject):
    characteristics = getattr(shelfobject, "shelfobjectequipmentcharacteristics", None)
    return {
        "object": shelfobject,
        "ch": characteristics,
        "plans": shelfobject.equipmentactivityplan_set.prefetch_related("responsible__user"),
        "calibrations": shelfobject.shelfobjectcalibrate_set.select_related("provider").order_by("-calibration_date"),
        "verifications": shelfobject.shelfobjectverification_set.select_related("responsible__user").order_by("-verification_date"),
        "maintenances": shelfobject.shelfobjectmaintenance_set.select_related("provider_of_maintenance")
        .prefetch_related("activities").order_by("-maintenance_date"),
        "failures": shelfobject.shelfobjectfailure_set.order_by("-failure_date"),
        "documents": shelfobject.equipmentdocument_set.select_related("document_type"),
        "trainings": shelfobject.shelfobjecttraining_set.order_by("-training_initial_date"),
        "history": shelfobject.shelfobjectobservation_set.order_by("-creation_date")[:100],
        "datetime": timezone.now(),
    }


@login_required
@permission_required("laboratory.view_shelfobject", raise_exception=True)
def equipment_life_record_pdf(request, org_pk, lab_pk, pk):
    scope(request, org_pk, lab_pk)
    shelfobject = get_object_or_404(
        ShelfObject, pk=pk, in_where_laboratory_id=lab_pk, object__type=Object.EQUIPMENT
    )
    context = life_record_context(shelfobject)
    context.update({"user": request.user, "title": _("Equipment life record")})
    html = get_template("laboratory/equipment/life_record_pdf.html").render(context)
    response = HttpResponse(html_to_pdf(html, base_url=request.build_absolute_uri()), content_type="application/pdf")
    code = context["ch"].internal_code if context["ch"] and context["ch"].internal_code else str(pk)
    response["Content-Disposition"] = 'attachment; filename="hoja_de_vida_%s.pdf"' % code
    return response
