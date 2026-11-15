"""Gráficos de las cartas de control (djgentelella ``LineChart``, Chart.js).

Desde djgentelella 0.7 los datasets aceptan cualquier opción de Chart.js: los límites van
discontinuos (``borderDash``), los puntos fuera de control en rojo
(``pointBackgroundColor`` por punto) y un registro sin límites deja un hueco (``None``).
Cada registro se dibuja con los límites que se le aplicaron, así que un recálculo se ve
como un escalón y no reescribe la historia.
"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from djgentelella.chartjs import LineChart
from djgentelella.groute import register_lookups
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from auth_and_perms.organization_utils import organization_can_change_laboratory, user_is_allowed_on_organization
from laboratory.models import ControlMeasurement, ControlMethod, ControlPoint, OrganizationStructure

OK_COLOR = "rgb(2, 128, 144)"
ALERT_COLOR = "rgb(216, 15, 53)"
LIMIT_COLOR = "rgb(229, 158, 64)"
CENTER_COLOR = "rgb(90, 90, 90)"
#: registros que trae la carta sin filtro de fechas, y tope con filtro
DEFAULT_WINDOW = 100
MAX_WINDOW = 2000


class ControlChartPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perms(
            ["laboratory.view_controlpoint", "laboratory.view_controlmeasurement"]
        )


class ControlChartBase:
    authentication_classes = [SessionAuthentication]
    permission_classes = [ControlChartPermission]
    #: atributo del registro con el valor graficado y prefijo de los límites
    value_field = "corrected_mean"
    limit_prefix = ""

    def list(self, request):
        raise Http404("Not found")

    def retrieve(self, request, pk):
        organization = get_object_or_404(OrganizationStructure, pk=request.query_params.get("organization"))
        user_is_allowed_on_organization(request.user, organization)
        self.point = get_object_or_404(
            ControlPoint.objects.select_related("method", "shelfobject__in_where_laboratory"),
            pk=pk, shelfobject__in_where_laboratory_id=request.query_params.get("laboratory"),
        )
        organization_can_change_laboratory(self.point.shelfobject.in_where_laboratory, organization, raise_exec=True)
        self.records = self.get_records(request)
        return Response(self.serializer_class(self.get_graph_data()).data)

    def get_records(self, request):
        """Los registros del rango ``from``/``to``; sin rango, los últimos ``DEFAULT_WINDOW``.

        Una carta con lectura diaria junta miles de puntos en pocos años: no se
        mandan todos al navegador.
        """
        from laboratory.equipment.control import ControlError, parse_date

        queryset = ControlMeasurement.objects.filter(point=self.point).select_related("limits")
        limits = {}
        for param, lookup in (("from", "measured_on__gte"), ("to", "measured_on__lte")):
            value = request.query_params.get(param)
            if value:
                try:
                    limits[lookup] = parse_date(value)
                except ControlError:
                    raise Http404("Invalid date")
        if limits:
            return list(queryset.filter(**limits).order_by("measured_on", "pk")[:MAX_WINDOW])
        return list(queryset.order_by("-measured_on", "-pk")[:DEFAULT_WINDOW])[::-1]

    def get_labels(self):
        return [record.measured_on.strftime("%d/%m/%Y") for record in self.records]

    def limit(self, record, name):
        if record.limits is None:
            return None
        return float(getattr(record.limits, self.limit_prefix + name))

    def get_datasets(self):
        values = [None if getattr(record, self.value_field) is None else float(getattr(record, self.value_field))
                  for record in self.records]
        colors = [ALERT_COLOR if record.out_of_control or record.out_of_acceptance else OK_COLOR
                  for record in self.records]
        line = {"fill": False, "borderWidth": 1, "pointRadius": 0, "spanGaps": False, "stepped": "middle"}
        return [
            {"label": str(self.series_label()), "data": values, "borderColor": OK_COLOR, "fill": False,
             "borderWidth": 2, "pointRadius": 4, "pointBackgroundColor": colors, "pointBorderColor": colors,
             "spanGaps": True},
            {"label": str(_("UCL")), "data": [self.limit(r, "ucl") for r in self.records],
             "borderColor": LIMIT_COLOR, "borderDash": [6, 4], **line},
            {"label": str(_("CL")), "data": [self.limit(r, "center") for r in self.records],
             "borderColor": CENTER_COLOR, **line},
            {"label": str(_("LCL")), "data": [self.limit(r, "lcl") for r in self.records],
             "borderColor": LIMIT_COLOR, "borderDash": [6, 4], **line},
        ]

    def get_title(self):
        return {"display": True, "text": "%s · %s" % (self.title(), self.point)}


@register_lookups(prefix="equipment_control_means", basename="equipmentcontrolmeanschart")
class ControlMeansChart(ControlChartBase, LineChart):

    def title(self):
        if self.point.method.chart_type == ControlMethod.I_MR:
            return _("Individuals chart")
        return _("Means chart")

    def series_label(self):
        return _("Corrected value") if self.point.method.chart_type == ControlMethod.I_MR else _("Corrected mean")


@register_lookups(prefix="equipment_control_ranges", basename="equipmentcontrolrangeschart")
class ControlRangesChart(ControlChartBase, LineChart):
    value_field = "range"
    limit_prefix = "range_"

    def limit(self, record, name):
        return super().limit(record, {"center": "center", "ucl": "ucl", "lcl": "lcl"}[name])

    def title(self):
        if self.point.method.chart_type == ControlMethod.I_MR:
            return _("Moving range chart")
        return _("Ranges chart")

    def series_label(self):
        return _("Moving range") if self.point.method.chart_type == ControlMethod.I_MR else _("Range")
