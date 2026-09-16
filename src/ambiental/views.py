from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ambiental.forms import (
    AmbientalReportForm,
    BuildingFilterForm,
    ConsumptionRecordForm,
    MeasurementPointForm,
    NormalizationBaseForm,
)
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure


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


@login_required
@permission_required("ambiental.view_consumptionrecord", raise_exception=True)
def consumptionrecord_list(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    context = {
        "org_pk": org_pk,
        "building_form": BuildingFilterForm(),
        "form_create": ConsumptionRecordForm(prefix="create", organization=organization),
        "form_update": ConsumptionRecordForm(prefix="update", organization=organization),
    }
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
