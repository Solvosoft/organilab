"""Generación idempotente de los reportes mensuales de precursores.

El reporte que se emite en un mes (`month`/`year`) resume los movimientos del
mes anterior (`month_belong`). Existe a lo sumo un reporte por laboratorio y
periodo, así que la tarea periódica, la acción del admin y el comando pueden
correr las veces que sea sin duplicar reportes ni consecutivos.
"""

from datetime import date

from django.db import transaction

from laboratory.models import Laboratory, PrecursorReport
from laboratory.task_utils import (
    build_precursor_report_from_reports,
    save_object_report_precursor,
)


def current_period(today=None):
    """Devuelve `(month, year, month_belong)` del reporte que toca emitir."""
    today = today or date.today()
    month_belong = 12 if today.month == 1 else today.month - 1
    return today.month, today.year, month_belong


def ensure_precursor_report(laboratory, today=None):
    """Crea el reporte del periodo si falta; devuelve `(reporte, creado)`."""
    month, year, month_belong = current_period(today)
    with transaction.atomic():
        # El bloqueo serializa las ejecuciones concurrentes sobre el mismo laboratorio.
        Laboratory.objects.select_for_update().filter(pk=laboratory.pk).first()
        existing = PrecursorReport.objects.filter(laboratory=laboratory, month=month, year=year).first()
        if existing:
            return existing, False

        previous_report = PrecursorReport.objects.filter(laboratory=laboratory).order_by("-year", "-month", "-consecutive").first()
        report = PrecursorReport.objects.create(month=month, year=year, laboratory=laboratory, month_belong=month_belong)
        save_object_report_precursor(report)
        build_precursor_report_from_reports(report, previous_report)
        return report, True


def ensure_precursor_reports(laboratories, today=None):
    """Asegura el reporte del periodo en cada laboratorio; devuelve cuántos creó."""
    created = 0
    for laboratory in laboratories:
        created += ensure_precursor_report(laboratory, today=today)[1]
    return created
