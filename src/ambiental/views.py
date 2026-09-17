from django.contrib.auth.decorators import login_required, permission_required
import datetime
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ambiental.forms import (
    AmbientalReportForm,
    BuildingFilterForm,
    ComparisonReportForm,
    DashboardFilterForm,
    IndicatorReportForm,
    ConsumptionRecordForm,
    MeasurementPointForm,
    NormalizationBaseForm,
)
from ambiental.ambiental_defaults import KEY_RESOURCE_TYPE, get_resource_info
from ambiental.indicators import compare_periods
from ambiental.models import ConsumptionRecord
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import Catalog, OrganizationStructure


@login_required
@permission_required("ambiental.view_measurementpoint", raise_exception=True)
def measurementpoint_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        "org_pk": org_pk,
        "form_create": MeasurementPointForm(prefix="create"),
        "form_update": MeasurementPointForm(prefix="update"),
    }
    return render(request, "ambiental/measurementpoint_list.html", context=context)


def consumption_context(request, org_pk, waste):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    return {
        "org_pk": org_pk,
        "waste": waste,
        "building_form": BuildingFilterForm(),
        "form_create": ConsumptionRecordForm(prefix="create", organization=organization),
        "form_update": ConsumptionRecordForm(prefix="update", organization=organization),
    }


@login_required
@permission_required("ambiental.view_consumptionrecord", raise_exception=True)
def consumptionrecord_list(request, org_pk):
    context = consumption_context(request, org_pk, waste=False)
    return render(request, "ambiental/consumptionrecord_list.html", context=context)


@login_required
@permission_required("ambiental.view_consumptionrecord", raise_exception=True)
def waste_list(request, org_pk):
    """La misma pantalla de consumos, acotada a los puntos y registros de residuos."""
    context = consumption_context(request, org_pk, waste=True)
    return render(request, "ambiental/consumptionrecord_list.html", context=context)


@login_required
@permission_required("ambiental.view_normalizationbase", raise_exception=True)
def normalizationbase_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        "org_pk": org_pk,
        "form_create": NormalizationBaseForm(prefix="create"),
        "form_update": NormalizationBaseForm(prefix="update"),
    }
    return render(request, "ambiental/normalizationbase_list.html", context=context)


REPORT_TITLES = {
    "report_consumption_detail": _("Consumption detail report"),
    "report_consumption_summary": _("Consumption summary report"),
    "report_consumption_cost": _("Consumption cost report"),
    "report_environmental_indicators": _("Environmental indicators report"),
    "report_consumption_comparison": _("Consumption comparison report"),
    "report_waste_manifest": _("Waste and manifests report"),
}


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("laboratory.do_report", raise_exception=True), name="dispatch"
)
@method_decorator(
    permission_required("ambiental.view_consumptionrecord", raise_exception=True),
    name="dispatch",
)
class AmbientalReportView(TemplateView):
    """Formulario de un reporte ambiental sobre la plantilla común de ``report``.

    La generación, la cola y la descarga son las de ``report``; aquí solo se elige
    qué reporte y con qué formulario.
    """

    template_name = "report/base_report_form_view.html"
    report_name = None
    form_class = AmbientalReportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_pk = self.kwargs["org_pk"]
        user_is_allowed_on_organization(self.request.user, org_pk)
        title = REPORT_TITLES[self.report_name]
        initial = {
            "name": slugify("%s %s" % (title, now().strftime("%Y-%m-%d"))),
            "title": title,
            "organization": org_pk,
            "report_name": self.report_name,
        }
        context.update(
            {
                "org_pk": org_pk,
                "title_view": title,
                # La plantilla común exige view_object (inventario); los permisos de
                # este reporte ya los verificó el decorador.
                "report_allowed": True,
                "form": self.form_class(initial=initial, org_pk=org_pk, user=self.request.user),
            }
        )
        return context


def month_bounds(date):
    start = date.replace(day=1)
    end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    return start, end


def latest_month_cards(organization, year, building=None):
    """Por recurso: el último mes con registros del año contra el mes anterior."""
    records = ConsumptionRecord.objects.filter(organization=organization, period_end__year=year)
    if building is not None:
        records = records.filter(point__building=building)
    cards = []
    for resource in Catalog.objects.filter(key=KEY_RESOURCE_TYPE, pk__in=records.values("point__resource_type")):
        last = records.filter(point__resource_type=resource).order_by("-period_end").first()
        current = month_bounds(last.period_end)
        previous = month_bounds(current[0] - datetime.timedelta(days=1))
        before, now_row = compare_periods(organization, resource, [previous, current], building)
        cards.append({
            "resource": resource.description,
            "icon": get_resource_info(resource)["icon"],
            "month": current[0],
            "quantity": now_row["quantity"],
            "unit": now_row["unit"],
            "mixed_units": now_row["mixed_units"],
            "percent": now_row["percent"],
            "cost": now_row["cost"],
        })
    return cards


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("ambiental.view_ambiental_dashboard", raise_exception=True),
    name="dispatch",
)
class AmbientalDashboard(TemplateView):
    template_name = "ambiental/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_pk = self.kwargs["org_pk"]
        organization = get_object_or_404(OrganizationStructure, pk=org_pk)
        user_is_allowed_on_organization(self.request.user, organization)
        form = DashboardFilterForm(self.request.GET or None, organization=organization)
        filters = {"org_pk": org_pk, "year": datetime.date.today().year}
        building = None
        if form.is_valid():
            data = form.cleaned_data
            filters["year"] = data["year"] or filters["year"]
            building = data["building"]
            for name in ("building", "resource_type", "normalizer"):
                if data[name] is not None:
                    filters[name] = data[name].pk
        query = "?" + urlencode(filters)
        context.update(
            {
                "org_pk": org_pk,
                "form": form if form.is_bound else DashboardFilterForm(organization=organization),
                "year": filters["year"],
                "cards": latest_month_cards(organization, filters["year"], building),
                "consumption_chart": reverse("ambientalmonthlyconsumptionchart-detail", kwargs={"pk": org_pk}) + query,
                "cost_chart": reverse("ambientalmonthlycostchart-detail", kwargs={"pk": org_pk}) + query,
                "ranking_chart": reverse("ambientalbuildingrankingchart-detail", kwargs={"pk": org_pk}) + query,
            }
        )
        return context
