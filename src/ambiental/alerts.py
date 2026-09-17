"""Evaluación de las reglas de alerta del proceso ``ambiental.consumption``.

Para cada punto de medición de la organización de la regla:

* **Variación porcentual**: el último período del punto contra el promedio de los
  meses anteriores (ventana ``ambiental.alert_window_months``), en la misma unidad.
* **Umbral absoluto**: el último período supera el valor de la regla.
* **Sin registro**: el punto lleva los meses de la regla sin ningún registro.

Una alerta por regla, punto y período (``unique_together``): correr la tarea dos veces
no duplica avisos.
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext as _

from ambiental.access import BuildingAccess
from ambiental.models import ConsumptionAlert, ConsumptionRecord, MeasurementPoint
from presentation.alerts import (
    TRIGGER_ABSOLUTE,
    TRIGGER_MISSING,
    TRIGGER_PERCENT,
    fire_alert,
    threshold_value,
)
from presentation.parameters import get_parameter
from risk_management.models_utils import add_months

PROCESS = "ambiental.consumption"
NOTIFICATION_CODE = "ambiental-consumption-alert"


def first_of_month(date):
    return date.replace(day=1)


def point_responsibles(point):
    """El encargado del edificio y los responsables de sus laboratorios."""
    return point_responsibles_of(point.building)


def building_recipient_filter(organization, building):
    """Los roles de la regla solo avisan a quien ve el edificio del punto.

    El encargado del edificio y los responsables de sus laboratorios se avisan siempre:
    son parte del edificio aunque no tengan un rol ambiental.
    """
    responsibles = set()

    def allowed(user):
        if not responsibles:
            responsibles.update(user.pk for user in point_responsibles_of(building))
        if user.pk in responsibles:
            return True
        return BuildingAccess(user, organization).has("ambiental.view_consumptionalert", building)

    return allowed


def point_responsibles_of(building):
    if building is None:
        return []
    user_ids = set(
        building.laboratories.filter(responsible__isnull=False).values_list("responsible", flat=True)
    )
    if building.manager_id:
        user_ids.add(building.manager_id)
    return list(get_user_model().objects.filter(pk__in=user_ids))


def raise_alert(rule, point, period, message, record=None, reference=None, registered=None, variation=None):
    alert, created = ConsumptionAlert.objects.get_or_create(
        rule=rule,
        point=point,
        period=period,
        defaults={
            "organization": rule.organization,
            "record": record,
            "reference_value": reference,
            "registered_value": registered,
            "variation_pct": variation,
            "level": rule.level,
            "message": message,
            "created_by": rule.created_by,
        },
    )
    if created:
        fire_alert(
            rule,
            message,
            obj=alert,
            responsible_users=point_responsibles(point),
            recipient_filter=building_recipient_filter(rule.organization, point.building),
            context={"point": point, "alert": alert},
            link=reverse("ambiental:consumptionalert_list", kwargs={"org_pk": rule.organization_id}),
        )
    return alert if created else None


def evaluate_rule(rule, today=None):
    today = today or datetime.date.today()
    trigger = rule.trigger.description
    threshold = threshold_value(rule)
    window = get_parameter(rule.organization, "ambiental.alert_window_months")
    points = MeasurementPoint.objects.filter(organization=rule.organization).select_related("building")
    raised = []
    for point in points:
        if trigger == TRIGGER_MISSING:
            limit = add_months(first_of_month(today), -threshold)
            if not ConsumptionRecord.objects.filter(point=point, period_end__gte=limit).exists():
                message = _("The measurement point %(point)s has no records for %(months)s months.") % {
                    "point": point, "months": threshold,
                }
                raised.append(raise_alert(rule, point, first_of_month(today), message))
            continue

        last = ConsumptionRecord.objects.filter(point=point).order_by("-period_end").first()
        if last is None:
            continue
        period = first_of_month(last.period_end)

        if trigger == TRIGGER_ABSOLUTE:
            if last.quantity > threshold:
                message = _("The measurement point %(point)s registered %(value)s %(unit)s in %(period)s, above the limit of %(limit)s.") % {
                    "point": point, "value": last.quantity.normalize(), "unit": last.unit,
                    "period": period.strftime("%m/%Y"), "limit": threshold,
                }
                raised.append(raise_alert(rule, point, period, message, record=last,
                                          reference=threshold, registered=last.quantity))
            continue

        if trigger == TRIGGER_PERCENT:
            history = list(
                ConsumptionRecord.objects.filter(
                    point=point, unit=last.unit,
                    period_end__gte=add_months(period, -window), period_end__lt=period,
                ).values_list("quantity", flat=True)
            )
            if not history:
                continue
            average = sum(history, Decimal(0)) / len(history)
            if average <= 0:
                continue
            variation = ((last.quantity - average) / average * 100).quantize(Decimal("0.01"))
            if variation > threshold:
                message = _("The measurement point %(point)s consumed %(value)s %(unit)s in %(period)s, %(variation)s%% over its average.") % {
                    "point": point, "value": last.quantity.normalize(), "unit": last.unit,
                    "period": period.strftime("%m/%Y"), "variation": variation,
                }
                raised.append(raise_alert(rule, point, period, message, record=last,
                                          reference=average.quantize(Decimal("0.0001")),
                                          registered=last.quantity, variation=variation))
    return [alert for alert in raised if alert is not None]
