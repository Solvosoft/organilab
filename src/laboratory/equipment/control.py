"""Registros de las cartas de control: cálculo, límites, evaluación y alertas (fase 3).

* ``register_measurement``: valida las n lecturas, calcula media, rango y media corregida
  (en I‑MR el rango es el móvil contra el registro anterior), la evalúa con los límites
  vigentes y dispara la alerta si queda fuera de control o de aceptación.
* ``recalculate_limits``: límites con un período de referencia elegido por el laboratorio.
  Guarda el historial (los anteriores dejan de estar vigentes) y reevalúa los registros
  desde el inicio del período.
* Registrar la acción tomada en un registro resuelve su alerta, con el registro como
  evidencia (``resolve_measurement_alerts``).
"""
import datetime

from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext as _

from laboratory.equipment import spc
from laboratory.models import ControlLimits, ControlMeasurement, ControlMethod

PROCESS = "laboratory.equipment_control"
TRIGGER_OUT_OF_CONTROL = "out_of_control"
NOTIFICATION_CODE = "equipment-control-alert"


class ControlError(ValueError):
    pass


def chart_type(point):
    return spc.I_MR if point.method.chart_type == ControlMethod.I_MR else spc.XBAR_R


def previous_measurement(point, measured_on, exclude_pk=None):
    """El registro anterior en la serie: fecha menor, o la misma fecha y registrado antes."""
    from django.db.models import Q

    earlier = Q(measured_on__lt=measured_on)
    if exclude_pk:
        earlier |= Q(measured_on=measured_on, pk__lt=exclude_pk)
    else:
        earlier |= Q(measured_on=measured_on)
    return ControlMeasurement.objects.filter(earlier, point=point).order_by("-measured_on", "-pk").first()


def compute(measurement):
    """Llena media, rango, media corregida y la evaluación de ``measurement`` (sin guardar)."""
    point = measurement.point
    n = point.method.subgroup_size
    values = measurement.values or []
    if len(values) != n:
        raise ControlError(_("This control point needs %(n)s readings per record.") % {"n": n})
    try:
        average, value_range, corrected = spc.subgroup_stats(values, point.correction)
    except Exception:
        raise ControlError(_("Every reading must be a number."))
    measurement.values = [str(spc.to_decimal(value)) for value in values]
    measurement.mean = average
    measurement.corrected_mean = corrected
    if chart_type(point) == spc.I_MR:
        previous = previous_measurement(point, measurement.measured_on, exclude_pk=measurement.pk)
        measurement.range = abs(corrected - previous.corrected_mean) if previous else None
    else:
        measurement.range = value_range
    limits = point.current_limits()
    measurement.limits = limits
    measurement.out_of_control, measurement.out_of_acceptance, _reasons = spc.evaluate(
        corrected, measurement.range, limits.as_dict() if limits else None, point.nominal_value, point.tolerance
    )
    return measurement


@transaction.atomic
def save_measurement(measurement, user=None):
    """Calcula, guarda y avisa; en I‑MR recalcula el rango móvil del registro siguiente."""
    compute(measurement)
    if measurement.organization_id is None:
        measurement.organization = measurement.point.organization
    if user is not None and measurement.created_by_id is None:
        measurement.created_by = user
    measurement.save()
    if chart_type(measurement.point) == spc.I_MR:
        following = (
            ControlMeasurement.objects.filter(point=measurement.point, measured_on__gte=measurement.measured_on)
            .exclude(pk=measurement.pk).order_by("measured_on", "pk").first()
        )
        if following is not None:
            compute(following)
            following.save()
    notify(measurement)
    if measurement.corrective_action:
        resolve_measurement_alerts(measurement, user)
    return measurement


@transaction.atomic
def recalculate_limits(point, baseline_from, baseline_to, user=None, notes=""):
    records = list(
        ControlMeasurement.objects.filter(point=point, measured_on__range=(baseline_from, baseline_to))
        .order_by("measured_on", "pk")
    )
    constants = point.method.constants()
    try:
        values = spc.limits(
            chart_type(point), [record.corrected_mean for record in records],
            [record.range for record in records if record.range is not None], constants,
        )
    except ValueError:
        raise ControlError(_("The reference period does not have enough records to calculate the limits."))
    ControlLimits.objects.filter(point=point, is_current=True).update(is_current=False)
    limits = ControlLimits.objects.create(
        point=point, organization=point.organization, created_by=user,
        baseline_from=baseline_from, baseline_to=baseline_to, subgroups=len(records),
        constants={name: str(value) for name, value in constants.items()}, correction=point.correction,
        notes=notes, **{name: spc.rounded(value, 8) for name, value in values.items()},
    )
    for record in ControlMeasurement.objects.filter(point=point, measured_on__gte=baseline_from).order_by("measured_on", "pk"):
        compute(record)
        record.save()
        notify(record)
    return limits


# --- Alertas -------------------------------------------------------------------------

def measurement_link(measurement):
    point = measurement.point
    shelfobject = point.shelfobject
    return reverse(
        "laboratory:equipment_control_point",
        kwargs={"org_pk": point.organization_id or shelfobject.in_where_laboratory.organization_id,
                "lab_pk": shelfobject.in_where_laboratory_id, "pk": shelfobject.pk, "point": point.pk},
    )


def measurement_message(measurement):
    point = measurement.point
    reasons = []
    if measurement.out_of_control:
        reasons.append(_("outside the control limits"))
    if measurement.out_of_acceptance:
        reasons.append(_("outside the acceptance criterion"))
    return _("%(point)s of %(equipment)s on %(date)s is %(reasons)s.") % {
        "point": point, "equipment": point.shelfobject.object.name,
        "date": measurement.measured_on.strftime("%d/%m/%Y"), "reasons": _(" and ").join(reasons),
    }


def notify(measurement):
    """Dispara las reglas del proceso de la organización si el registro quedó fuera."""
    if not (measurement.out_of_control or measurement.out_of_acceptance) or measurement.corrective_action:
        return []
    from presentation.alerts import fire_alert
    from presentation.models import AlertRule

    point = measurement.point
    laboratory = point.shelfobject.in_where_laboratory
    organizations = laboratory.organization.ancestors(include_self=True)
    characteristics = getattr(point.shelfobject, "shelfobjectequipmentcharacteristics", None)
    responsibles = [profile.user for profile in (
        measurement.responsible, characteristics.custodian if characteristics else None,
    ) if profile is not None]
    if laboratory.responsible_id:
        responsibles.append(laboratory.responsible)
    events = []
    for rule in AlertRule.objects.filter(process=PROCESS, is_active=True, organization__in=organizations):
        events.append(fire_alert(
            rule, measurement_message(measurement), obj=measurement, responsible_users=responsibles,
            context={"point": point, "measurement": measurement}, link=measurement_link(measurement),
            dedupe_key="control-measurement:%s" % measurement.pk,
        ))
    return events


def resolve_measurement_alerts(measurement, user=None):
    from presentation.alerts import resolve_alert

    return resolve_alert(measurement, resolution=measurement, user=user)


def evaluate_rule(rule, **kwargs):
    """Las alertas de control se disparan al registrar; la tarea programada no hace nada."""
    return []


def register_alerts():
    from djgentelella.alerts import register_trigger
    from django.utils.translation import gettext_lazy

    from presentation.alerts import register_alert_process

    register_trigger(TRIGGER_OUT_OF_CONTROL, gettext_lazy("Out of control or acceptance"), {})
    register_alert_process(
        PROCESS,
        label=gettext_lazy("Equipment control charts"),
        evaluator="laboratory.equipment.control.evaluate_rule",
        triggers=(TRIGGER_OUT_OF_CONTROL,),
        permission="laboratory.view_controlmeasurement",
        notification_code=NOTIFICATION_CODE,
    )


def parse_date(value):
    if isinstance(value, datetime.date):
        return value
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    raise ControlError(_("Enter a valid date."))
