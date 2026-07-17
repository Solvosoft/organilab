import json
from io import BytesIO

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.forms import CatalogForm
from laboratory.models import (
    Catalog,
    Laboratory,
    OrganizationStructure,
    ShelfObject,
)
from laboratory.utils import (
    check_user_access_kwargs_org_lab,
    get_user_laboratories,
    organilab_logentry,
)
from laboratory.views.djgeneric import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    ReportListView,
    UpdateView,
)
from pending_tasks.utils import create_pending_task
from report.utils import create_notification
from risk_management.forms import (
    IPERAssessmentForm,
    IPERHazardForm,
    IPERHistoryFilterForm,
    IPERObservationForm,
)
from openpyxl import Workbook
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

from risk_management.iper_defaults import (
    CONSEQUENCE_LEVELS,
    HAZARD_CATEGORIES,
    KEY_CONSEQUENCE,
    KEY_HAZARD_CATEGORY,
    KEY_PROBABILITY,
    KEY_RISK_LEVEL,
    PROBABILITY_LEVELS,
    RISK_LEVEL_BOOTSTRAP,
    RISK_LEVELS,
    RISK_MATRIX,
)
from risk_management.models import (
    IPERAssessment,
    IPERHazard,
    RiskZone,
)
from risk_management.models_utils import add_months, get_iper_config

IPER_CATALOG_KEYS = {
    KEY_HAZARD_CATEGORY,
    KEY_PROBABILITY,
    KEY_CONSEQUENCE,
    KEY_RISK_LEVEL,
}


def _risk_summary(counts):
    """Construye la lista [{level, color, count}] ordenada por prioridad."""
    return [
        {
            "level": level,
            "color": RISK_LEVEL_BOOTSTRAP.get(level, "secondary"),
            "count": counts.get(level, 0),
        }
        for level in RISK_LEVELS
    ]


# --- listado --------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.view_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERAssessmentList(ListView):
    model = IPERAssessment
    template_name = "risk_management/iper_list.html"
    paginate_by = 20

    def get_queryset(self):
        org = self.kwargs["org_pk"]
        queryset = super().get_queryset().filter(organization__pk=org)
        if not self.request.user.has_perm("risk_management.view_all_iper"):
            labs = get_user_laboratories(self.request.user)
            queryset = queryset.filter(laboratory__in=labs)
        q = self.request.GET.get("q", "")
        if q:
            queryset = queryset.filter(
                Q(laboratory__name__icontains=q, is_anonymous=False)
                | Q(responsible__username__icontains=q)
            ).distinct()
        return queryset.select_related("laboratory", "responsible")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "")
        context["q"] = q
        context["pgparams"] = "?q=%s&" % q if q else "?"
        context["can_view_all"] = self.request.user.has_perm(
            "risk_management.view_all_iper"
        )
        return context


# --- crear / editar cabecera ----------------------------------------------
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.add_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERAssessmentCreate(CreateView):
    model = IPERAssessment
    form_class = IPERAssessmentForm
    template_name = "risk_management/iper_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["org_pk"] = self.org
        return kwargs

    def form_valid(self, form):
        assessment = form.save(commit=False)
        assessment.organization = OrganizationStructure.objects.filter(
            pk=self.org
        ).first()
        assessment.created_by = self.request.user
        assessment.responsible = assessment.laboratory.responsible or self.request.user
        assessment.version = 1
        assessment.source = IPERAssessment.ON_DEMAND
        cfg = get_iper_config(assessment.organization, assessment.laboratory)
        if cfg:
            assessment.due_date = add_months(
                assessment.assessment_date, cfg.period_months
            )
        assessment.save()
        self.object = assessment
        organilab_logentry(
            self.request.user,
            assessment,
            ADDITION,
            "iperassessment",
            changed_data=["laboratory", "assessment_date", "responsible"],
            change_message=_("Created IPER assessment for laboratory '%(lab)s'")
            % {"lab": assessment.laboratory.name},
            relobj=[assessment.laboratory],
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "riskmanagement:iper_detail",
            kwargs={"org_pk": self.org, "pk": self.object.pk},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.change_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERAssessmentUpdate(UpdateView):
    model = IPERAssessment
    form_class = IPERAssessmentForm
    template_name = "risk_management/iper_form.html"

    def get_queryset(self):
        return super().get_queryset().filter(organization__pk=self.kwargs["org_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["org_pk"] = self.org
        return kwargs

    def form_valid(self, form):
        dev = super().form_valid(form)
        organilab_logentry(
            self.request.user,
            self.object,
            CHANGE,
            "iperassessment",
            changed_data=form.changed_data,
            change_message=_("Updated IPER assessment for laboratory '%(lab)s'")
            % {"lab": self.object.laboratory.name},
            relobj=[self.object.laboratory],
        )
        return dev

    def get_success_url(self):
        return reverse(
            "riskmanagement:iper_detail",
            kwargs={"org_pk": self.org, "pk": self.object.pk},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.delete_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERAssessmentDelete(DeleteView):
    model = IPERAssessment

    def get_queryset(self):
        return super().get_queryset().filter(organization__pk=self.kwargs["org_pk"])

    def form_valid(self, form):
        organilab_logentry(
            self.request.user,
            self.object,
            DELETION,
            "iperassessment",
            changed_data=["laboratory", "assessment_date"],
            change_message=_("Deleted IPER assessment for laboratory '%(lab)s'")
            % {"lab": self.object.laboratory.name},
            relobj=[self.object.laboratory],
        )
        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("riskmanagement:iper_list", kwargs={"org_pk": self.org})


# --- detalle (peligros + observaciones) -----------------------------------
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.view_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERAssessmentDetail(DetailView):
    model = IPERAssessment
    template_name = "risk_management/iper_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(organization__pk=self.kwargs["org_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hazard_form"] = IPERHazardForm(
            render_type="as_p",
        )
        context["observation_form"] = IPERObservationForm(
            render_type="as_p",
        )
        context["hazards"] = self.object.hazards.select_related(
            "category", "probability", "consequence", "risk_level"
        )
        context["risk_summary"] = _risk_summary(self.object.risk_level_counts())
        context["observations"] = self.object.observations.select_related("author")
        context["can_observe"] = self.request.user.has_perm(
            "risk_management.add_iperobservation"
        )
        context["can_edit"] = (
            self.request.user.has_perm("risk_management.add_iperhazard")
            and self.object.status != IPERAssessment.COMPLETED
        )
        context["can_delete_hazard"] = (
            self.request.user.has_perm("risk_management.delete_iperhazard")
            and self.object.status != IPERAssessment.COMPLETED
        )
        context["help_url"] = reverse(
            "riskmanagement:iper_lab_help",
            kwargs={"org_pk": self.org, "lab_pk": self.object.laboratory_id},
        )
        context["hazard_category_help"] = json.dumps(
            {
                k: {
                    "emoji": v["emoji"],
                    "description": str(v["description"]),
                    "examples": [str(e) for e in v["examples"]],
                }
                for k, v in HAZARD_CATEGORIES.items()
            },
            ensure_ascii=False,
        )
        context["probability_help"] = json.dumps(
            {k: str(v["help"]) for k, v in PROBABILITY_LEVELS.items()},
            ensure_ascii=False,
        )
        context["consequence_help"] = json.dumps(
            {k: str(v["help"]) for k, v in CONSEQUENCE_LEVELS.items()},
            ensure_ascii=False,
        )
        matrix_nested = {}
        for (prob, cons), level in RISK_MATRIX.items():
            matrix_nested.setdefault(prob, {})[cons] = {
                "level": level,
                "color": RISK_LEVEL_BOOTSTRAP.get(level, "secondary"),
            }
        context["risk_matrix_data"] = json.dumps(
            {
                "matrix": matrix_nested,
                "probability_order": list(PROBABILITY_LEVELS.keys()),
                "probability_short": {
                    k: v["short"] for k, v in PROBABILITY_LEVELS.items()
                },
                "consequence_order": list(CONSEQUENCE_LEVELS.keys()),
                "consequence_short": {
                    k: v["short"] for k, v in CONSEQUENCE_LEVELS.items()
                },
            },
            ensure_ascii=False,
        )
        return context


# --- anonimato -----------------------------------------------------------
@login_required
@permission_required("risk_management.change_iperassessment", raise_exception=True)
def iper_toggle_anonymous(request, org_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    assessment = get_object_or_404(IPERAssessment, pk=pk, organization__pk=org_pk)
    assessment.is_anonymous = not assessment.is_anonymous
    assessment.save(update_fields=["is_anonymous"])
    organilab_logentry(
        request.user,
        assessment,
        CHANGE,
        "iperassessment",
        changed_data=["is_anonymous"],
        change_message=_("Toggled anonymous mode for IPER assessment")
        % {},
        relobj=[assessment.laboratory],
    )
    return redirect(
        reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": pk})
    )


# --- estados: completar / reabrir -----------------------------------------
@login_required
@permission_required("risk_management.change_iperassessment", raise_exception=True)
def iper_toggle_status(request, org_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    assessment = get_object_or_404(IPERAssessment, pk=pk, organization__pk=org_pk)
    if assessment.status == IPERAssessment.DRAFT:
        assessment.status = IPERAssessment.COMPLETED
    elif assessment.status == IPERAssessment.COMPLETED:
        assessment.status = IPERAssessment.DRAFT
    else:
        messages.error(
            request, _("Obsolete IPER assessments cannot change status.")
        )
        return redirect(
            reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": pk})
        )
    assessment.save(update_fields=["status"])
    organilab_logentry(
        request.user,
        assessment,
        CHANGE,
        "iperassessment",
        changed_data=["status"],
        change_message=_("Changed IPER assessment status to '%(status)s'")
        % {"status": assessment.get_status_display()},
        relobj=[assessment.laboratory],
    )
    return redirect(
        reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": pk})
    )


# --- peligros: agregar / editar / borrar ----------------------------------
@login_required
@permission_required("risk_management.change_iperassessment", raise_exception=True)
def iper_hazard_action(request, org_pk, assessment_pk, pk=None):
    user_is_allowed_on_organization(request.user, org_pk)
    assessment = get_object_or_404(
        IPERAssessment, pk=assessment_pk, organization__pk=org_pk
    )
    if assessment.status == IPERAssessment.COMPLETED:
        messages.error(
            request,
            _("Cannot modify hazards while the IPER assessment is completed."),
        )
        return redirect(
            reverse(
                "riskmanagement:iper_detail",
                kwargs={"org_pk": org_pk, "pk": assessment_pk},
            )
        )
    hazard = None
    if pk:
        hazard = get_object_or_404(IPERHazard, pk=pk, assessment=assessment)
    if request.method == "POST":
        form = IPERHazardForm(request.POST, instance=hazard)
        if form.is_valid():
            hazard = form.save(commit=False)
            hazard.assessment = assessment
            hazard.save()
            form.save_m2m()
            action = CHANGE if pk else ADDITION
            action_msg = _("Updated") if pk else _("Created")
            organilab_logentry(
                request.user,
                hazard,
                action,
                "iperhazard",
                changed_data=form.changed_data,
                change_message=_("%(action)s hazard '%(desc)s' in IPER assessment")
                % {"action": action_msg, "desc": hazard.description[:50]},
                relobj=[assessment.laboratory],
            )
    return redirect(
        reverse(
            "riskmanagement:iper_detail",
            kwargs={"org_pk": org_pk, "pk": assessment_pk},
        )
    )


@login_required
@permission_required("risk_management.change_iperassessment", raise_exception=True)
def iper_hazard_delete(request, org_pk, assessment_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    assessment = get_object_or_404(
        IPERAssessment, pk=assessment_pk, organization__pk=org_pk
    )
    if assessment.status == IPERAssessment.COMPLETED:
        messages.error(
            request,
            _("Cannot modify hazards while the IPER assessment is completed."),
        )
        return redirect(
            reverse(
                "riskmanagement:iper_detail",
                kwargs={"org_pk": org_pk, "pk": assessment_pk},
            )
        )
    hazard = get_object_or_404(IPERHazard, pk=pk, assessment=assessment)
    organilab_logentry(
        request.user,
        hazard,
        DELETION,
        "iperhazard",
        changed_data=["description"],
        change_message=_("Deleted hazard '%(desc)s' from IPER assessment")
        % {"desc": hazard.description[:50]},
        relobj=[assessment.laboratory],
    )
    hazard.delete()
    return redirect(
        reverse(
            "riskmanagement:iper_detail",
            kwargs={"org_pk": org_pk, "pk": assessment_pk},
        )
    )


# --- observaciones del analista -------------------------------------------
@login_required
@permission_required("risk_management.add_iperobservation", raise_exception=True)
def iper_observation_add(request, org_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    assessment = get_object_or_404(IPERAssessment, pk=pk, organization__pk=org_pk)
    if request.method == "POST":
        form = IPERObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.assessment = assessment
            observation.author = request.user
            observation.save()
            organilab_logentry(
                request.user,
                observation,
                ADDITION,
                "iperobservation",
                changed_data=["text"],
                change_message=_("Added observation to IPER assessment"),
                relobj=[assessment.laboratory],
            )
            recipient = assessment.responsible or assessment.created_by
            if recipient and recipient != request.user:
                create_notification(
                    recipient,
                    _("A new observation was added to the IPER assessment of %s")
                    % assessment.laboratory,
                    reverse(
                        "riskmanagement:iper_detail",
                        kwargs={"org_pk": org_pk, "pk": pk},
                    ),
                )
    return redirect(
        reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": pk})
    )


# --- versionado: clonar para actualizar -----------------------------------
@login_required
@permission_required("risk_management.add_iperassessment", raise_exception=True)
def iper_clone_for_update(request, org_pk, pk):
    user_is_allowed_on_organization(request.user, org_pk)
    previous = get_object_or_404(IPERAssessment, pk=pk, organization__pk=org_pk)
    if previous.status == IPERAssessment.COMPLETED:
        messages.error(
            request,
            _("Reopen this completed IPER assessment before creating a new version."),
        )
        return redirect(
            reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": pk})
        )
    clean = request.GET.get("clean") == "1"

    new = IPERAssessment(
        organization=previous.organization,
        laboratory=previous.laboratory,
        assessment_date=now().date(),
        responsible=previous.responsible or request.user,
        created_by=request.user,
        status=IPERAssessment.DRAFT,
        version=previous.version + 1,
        previous=previous,
        source=IPERAssessment.ON_DEMAND,
    )
    cfg = get_iper_config(previous.organization, previous.laboratory)
    if cfg:
        new.due_date = add_months(new.assessment_date, cfg.period_months)
    new.save()

    if not clean:
        for hazard in previous.hazards.all():
            shelfobjects = list(hazard.related_shelfobjects.all())
            hazard.pk = None
            hazard.assessment = new
            hazard.save()
            if shelfobjects:
                hazard.related_shelfobjects.set(shelfobjects)

    previous.status = IPERAssessment.OBSOLETE
    previous.save()
    organilab_logentry(
        request.user,
        new,
        ADDITION,
        "iperassessment",
        changed_data=["laboratory", "version", "previous"],
        change_message=_("Cloned IPER assessment to version %(version)s")
        % {"version": new.version},
        relobj=[new.laboratory],
    )
    return redirect(
        reverse("riskmanagement:iper_detail", kwargs={"org_pk": org_pk, "pk": new.pk})
    )


# --- solicitud por zona de riesgo -----------------------------------------
@login_required
@permission_required("risk_management.request_iper", raise_exception=True)
def iper_request_for_zone(request, org_pk, risk_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    risk = get_object_or_404(RiskZone, pk=risk_pk, organization__pk=org_pk)
    link = reverse("riskmanagement:iper_list", kwargs={"org_pk": org_pk})
    count = 0
    for lab in risk.laboratories.all():
        responsible = lab.responsible
        if responsible is None:
            continue
        profile = getattr(responsible, "profile", None)
        if profile is None:
            continue
        create_pending_task(
            request.user,
            _("Update the IPER risk assessment"),
            [],
            description=_("Please fill or update the IPER for laboratory %(lab)s")
            % {"lab": lab.name},
            profile=profile,
            link=link,
            notify=True,
        )
        count += 1
    messages.success(
        request,
        _("IPER update requested to %(count)d laboratory responsibles.")
        % {"count": count},
    )
    return redirect(
        reverse(
            "riskmanagement:riskzone_detail", kwargs={"org_pk": org_pk, "pk": risk_pk}
        )
    )


# --- historial / export ---------------------------------------------------
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.view_iperassessment", raise_exception=True),
    name="dispatch",
)
class IPERHistory(ReportListView):
    model = IPERHazard
    template_name = "risk_management/iper_history.html"
    pdf_template = "risk_management/iper_pdf.html"
    file_name = "iper_history"

    def get_queryset(self):
        org = self.kwargs["org_pk"]
        queryset = IPERHazard.objects.filter(
            assessment__organization__pk=org
        ).select_related(
            "assessment__laboratory",
            "category",
            "probability",
            "consequence",
            "risk_level",
        )
        if not self.request.user.has_perm("risk_management.view_all_iper"):
            labs = get_user_laboratories(self.request.user)
            queryset = queryset.filter(assessment__laboratory__in=labs)
        form = IPERHistoryFilterForm(self.request.GET or None)
        if form.is_valid():
            cd = form.cleaned_data
            if cd.get("category"):
                queryset = queryset.filter(category=cd["category"])
            if cd.get("risk_level"):
                queryset = queryset.filter(risk_level=cd["risk_level"])
            if cd.get("date_from"):
                queryset = queryset.filter(assessment__assessment_date__gte=cd["date_from"])
            if cd.get("date_to"):
                queryset = queryset.filter(assessment__assessment_date__lte=cd["date_to"])
        return queryset.order_by("-assessment__assessment_date", "-risk_priority")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = IPERHistoryFilterForm(self.request.GET or None)
        counts = {level: 0 for level in RISK_LEVELS}
        for hazard in context["object_list"]:
            if hazard.risk_level_id:
                desc = hazard.risk_level.description
                counts[desc] = counts.get(desc, 0) + 1
        context["risk_summary"] = _risk_summary(counts)
        context["pgparams"] = self.request.GET.urlencode()
        return context

    # openpyxl hex fills per risk level
    _RISK_FILLS = {
        "Trivial":      PatternFill("solid", fgColor="92D050"),
        "Tolerable":    PatternFill("solid", fgColor="00B0F0"),
        "Moderado":     PatternFill("solid", fgColor="FFFF00"),
        "Importante":   PatternFill("solid", fgColor="FF9900"),
        "Intolerable":  PatternFill("solid", fgColor="FF0000"),
    }

    def get_book(self, context):
        # kept for ODS/XLS fallback (no styling)
        headers = [
            str(_("Date")), str(_("Laboratory")), str(_("Classification")),
            str(_("Hazard")), str(_("Location")), str(_("Probability")),
            str(_("Consequence")), str(_("Risk level")), str(_("Controls")),
        ]
        rows = [headers]
        anonymous_label = str(_("Anonymous"))
        for hazard in self.get_queryset():
            lab_name = (
                anonymous_label
                if hazard.assessment.is_anonymous
                else hazard.assessment.laboratory.name
            )
            rows.append([
                str(hazard.assessment.assessment_date),
                lab_name,
                str(hazard.category) if hazard.category_id else "",
                hazard.description,
                hazard.location,
                str(hazard.probability) if hazard.probability_id else "",
                str(hazard.consequence) if hazard.consequence_id else "",
                str(hazard.risk_level) if hazard.risk_level_id else "",
                hazard.controls,
            ])
        return rows

    def get_xlsx(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        anonymous_label = str(_("Anonymous"))

        wb = Workbook()
        ws = wb.active
        ws.title = str(_("IPER history"))

        headers = [
            str(_("Date")), str(_("Laboratory")), str(_("Classification")),
            str(_("Hazard")), str(_("Location")), str(_("Probability")),
            str(_("Consequence")), str(_("Risk level")), str(_("Controls")),
        ]

        header_fill = PatternFill("solid", fgColor="1F4E79")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        thin = Side(border_style="thin", color="BFBFBF")
        cell_border = Border(top=thin, left=thin, right=thin, bottom=thin)

        ws.append(headers)
        for col_idx, _hdr in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = cell_border

        ws.row_dimensions[1].height = 30
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        # column widths (chars)
        col_widths = [12, 24, 20, 45, 20, 14, 22, 16, 45]

        wrap_align = Alignment(vertical="top", wrap_text=True)
        center_align = Alignment(horizontal="center", vertical="top")

        for row_idx, hazard in enumerate(self.get_queryset(), start=2):
            lab_name = (
                anonymous_label
                if hazard.assessment.is_anonymous
                else hazard.assessment.laboratory.name
            )
            risk_desc = str(hazard.risk_level) if hazard.risk_level_id else ""
            row_data = [
                hazard.assessment.assessment_date,
                lab_name,
                str(hazard.category) if hazard.category_id else "",
                hazard.description or "",
                hazard.location or "",
                str(hazard.probability) if hazard.probability_id else "",
                str(hazard.consequence) if hazard.consequence_id else "",
                risk_desc,
                hazard.controls or "",
            ]
            ws.append(row_data)

            for col_idx, value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = cell_border
                # wrap long text columns
                if col_idx in (4, 5, 9):
                    cell.alignment = wrap_align
                else:
                    cell.alignment = center_align

            # color risk level cell
            risk_cell = ws.cell(row=row_idx, column=8)
            risk_fill = self._RISK_FILLS.get(risk_desc)
            if risk_fill:
                risk_cell.fill = risk_fill
                # dark text on yellow/green, white on orange/red
                dark = risk_desc in ("Trivial", "Tolerable", "Moderado")
                risk_cell.font = Font(bold=True, color="000000" if dark else "FFFFFF")

        for col_idx, width in enumerate(col_widths, start=1):
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        from django.http import HttpResponse
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{self.get_file_name(request)}.xlsx"'
        )
        return response


# --- dashboard del analista -----------------------------------------------
@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("risk_management.view_iper_dashboard", raise_exception=True),
    name="dispatch",
)
class IPERDashboard(TemplateView):
    template_name = "risk_management/iper_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_pk = self.kwargs["org_pk"]
        context["org_pk"] = org_pk
        extra = f"?org_pk={org_pk}"
        context["risklevelchart"] = (
            reverse("iperrisklevelchart-detail", kwargs={"pk": org_pk}) + extra
        )
        context["hazardcategorychart"] = (
            reverse("iperhazardcategorychart-detail", kwargs={"pk": org_pk}) + extra
        )
        context["compliancechart"] = (
            reverse("ipercompliancechart-detail", kwargs={"pk": org_pk}) + extra
        )
        return context


# --- ayuda contextual (inventario + peligros SGA del lab) ------------------
@login_required
@permission_required("risk_management.view_iperassessment", raise_exception=True)
def iper_lab_help(request, org_pk, lab_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    lab = get_object_or_404(Laboratory, pk=lab_pk)
    items = []
    queryset = ShelfObject.objects.filter(in_where_laboratory=lab).select_related(
        "object"
    )[:500]
    for shelfobject in queryset:
        obj = shelfobject.object
        if obj is None:
            continue
        hcodes = []
        try:
            chars = obj.sustancecharacteristics
            if chars is not None:
                hcodes = list(chars.h_code.values_list("code", flat=True))
        except Exception:
            hcodes = []
        items.append(
            {
                "name": obj.name,
                "type": obj.get_type_display(),
                "is_dangerous": obj.is_dangerous,
                "h_codes": hcodes,
            }
        )
    categories = [
        {"name": name, "emoji": data["emoji"]}
        for name, data in HAZARD_CATEGORIES.items()
    ]
    return JsonResponse(
        {"laboratory": lab.name, "items": items, "categories": categories}
    )


# --- catálogo IPER (solo org raíz) ----------------------------------------
@login_required
@permission_required("risk_management.manage_iper_catalog", raise_exception=True)
def iper_catalog_add(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    if organization.parent_id is not None:
        return JsonResponse(
            {
                "ok": False,
                "title": _("Not allowed"),
                "message": _("Only the root organization can manage the IPER catalog."),
            },
            status=403,
        )
    key = request.GET.get("key") or request.POST.get("key")
    if key not in IPER_CATALOG_KEYS:
        raise Http404()
    url = reverse("riskmanagement:iper_catalog_add", kwargs={"org_pk": org_pk})
    if request.method == "POST":
        form = CatalogForm(request.POST, initial={"key": key})
        if form.is_valid():
            instance = form.save()
            return JsonResponse(
                {"ok": True, "id": instance.pk, "text": instance.description}
            )
        return JsonResponse(
            {"ok": False, "title": _("ERROR"), "message": _("Data is not valid")}
        )
    form = CatalogForm(initial={"key": key})
    data = {
        "ok": True,
        "title": _("Add IPER catalog value"),
        "message": render_to_string(
            "risk_management/iper_catalog_add.html",
            context={"form": form, "url": url + "?key=" + key, "request": request},
        ),
    }
    return JsonResponse(data)
