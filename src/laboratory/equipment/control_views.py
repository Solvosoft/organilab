"""Pantallas de las cartas de control: métodos de la organización y la carta de un punto."""
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from laboratory.equipment.forms import (
    ChartRangeForm,
    ControlMeasurementForm,
    ControlMethodForm,
    FixedLimitsForm,
    RecalculateLimitsForm,
)
from laboratory.equipment.charts import DEFAULT_WINDOW
from laboratory.equipment.import_views import scope
from laboratory.models import ControlPoint


@login_required
@permission_required(["laboratory.view_controlmethod"], raise_exception=True)
def equipment_control_methods(request, org_pk, lab_pk):
    scope(request, org_pk, lab_pk)
    context = {
        "org_pk": org_pk, "lab_pk": lab_pk, "laboratory": lab_pk,
        # En el contexto y no con {% url ... as %}: esas variables no cruzan de bloque.
        "list_url": reverse("laboratory:api-equipment-control-method-list", kwargs={"org_pk": org_pk, "lab_pk": lab_pk}),
        "detail_url": reverse("laboratory:api-equipment-control-method-detail",
                              kwargs={"org_pk": org_pk, "lab_pk": lab_pk, "pk": 0}),
        "create_form": ControlMethodForm(prefix="create_method"),
        "update_form": ControlMethodForm(prefix="update_method"),
    }
    return render(request, "laboratory/equipment/control_methods.html", context)


@login_required
@permission_required(["laboratory.view_controlpoint", "laboratory.view_controlmeasurement"], raise_exception=True)
def equipment_control_point(request, org_pk, lab_pk, pk, point):
    scope(request, org_pk, lab_pk)
    point = get_object_or_404(
        ControlPoint.objects.select_related("method", "shelfobject__object"),
        pk=point, shelfobject_id=pk, shelfobject__in_where_laboratory_id=lab_pk,
    )
    form_scope = {"org_pk": org_pk, "lab_pk": lab_pk, "shelfobject": pk}
    measurement_kwargs = {"org_pk": org_pk, "lab_pk": lab_pk, "shelfobject": pk, "point": point.pk}
    chart_query = "?organization=%s&laboratory=%s" % (org_pk, lab_pk)
    # Sin rango la carta trae los últimos registros; con rango, los de esas fechas.
    range_form = ChartRangeForm(request.GET or None, prefix="chart")
    if range_form.is_bound and range_form.is_valid():
        for param, name in (("from", "date_from"), ("to", "date_to")):
            if range_form.cleaned_data.get(name):
                chart_query += "&%s=%s" % (param, range_form.cleaned_data[name].isoformat())
    context = {
        "org_pk": org_pk, "lab_pk": lab_pk, "laboratory": lab_pk, "pk": pk,
        "point": point,
        "limits": point.current_limits(),
        "limits_history": point.controllimits_set.all()[:20],
        "create_form": ControlMeasurementForm(prefix="create_measurement", **form_scope),
        "update_form": ControlMeasurementForm(prefix="update_measurement", **form_scope),
        "limits_form": RecalculateLimitsForm(prefix="limits"),
        "fixed_limits_form": FixedLimitsForm(prefix="fixed"),
        "range_form": range_form,
        "chart_window": DEFAULT_WINDOW,
        "list_url": reverse("laboratory:api-equipment-control-measurement-list", kwargs=measurement_kwargs),
        "detail_url": reverse("laboratory:api-equipment-control-measurement-detail", kwargs={**measurement_kwargs, "pk": 0}),
        "means_chart": reverse("equipmentcontrolmeanschart-detail", kwargs={"pk": point.pk}) + chart_query,
        "ranges_chart": reverse("equipmentcontrolrangeschart-detail", kwargs={"pk": point.pk}) + chart_query,
    }
    return render(request, "laboratory/equipment/control_point.html", context)
