# encoding: utf-8
"""
Created on 26/12/2016

@author: luisza
"""
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from laboratory.api.serializers import PrecursorSerializer
from laboratory.models import (
    Object,
    Furniture,
    ShelfObject,
    PrecursorReport,
    Shelf,
    PrecursorReportValues,
)
from laboratory.models import ObjectLogChange
from laboratory.views.djgeneric import ListView, ReportListView
from report.forms import (
    ReportForm,
    ObjectLogChangeBaseForm,
    ValidateObjectTypeForm,
    DiscardShelfForm,
    RiskZoneReportForm,
    ReactiveStockReportForm,
    LaboratoryRoomReportForm,
    ValidateFurnitureForm,
    PrecursorFilterForm,
    CompatibilityReportForm,
    HazardMapReportForm,
    PrecursorReportValuesViewForm,
)
from laboratory.models import Laboratory
from risk_management.models import RiskZone


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class ObjectList(ListView):
    model = Object
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(ObjectList, self).get_context_data(**kwargs)
        type_id = ""
        title_view = _("Objects Report")
        title_by_object = {
            "0": _("Reactive Objects Report"),
            "1": _("Material Objects Report"),
            "2": _("Equipment Objects Report"),
        }

        if self.request.method == "GET":
            if "type_id" in self.request.GET:
                id = self.request.GET["type_id"]
                if id.isalpha() or id not in title_by_object:
                    raise Http404(_("Page not found"))
            objecttypeform = ValidateObjectTypeForm(self.request.GET)

            if objecttypeform.is_valid():
                type_id = objecttypeform.cleaned_data["type_id"]

        if type_id in title_by_object:
            title_view = title_by_object[type_id]

        context.update(
            {
                "title_view": title_view,
                "report_urlnames": ["reports_objects_list"],
                "form": ReportForm(
                    initial={
                        "name": slugify(
                            title_view + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title_view,
                        "organization": self.org,
                        "report_name": "report_objects",
                        "object_type": type_id,
                    }
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class LimitedShelfObjectList(ListView):
    model = ShelfObject
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(LimitedShelfObjectList, self).get_context_data(**kwargs)
        title = _("Limited Shelf Objects Report")
        context["title_view"] = title
        context["report_urlnames"] = [
            "reports_limited_shelf_objects_list",
            "reports_limited_shelf_objects",
        ]
        context["form"] = ReportForm(
            initial={
                "name": slugify(title + " " + now().strftime("%x").replace("/", "-")),
                "title": title,
                "organization": self.org,
                "report_name": "report_limit_objects",
                "laboratory": self.lab,
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class ReactivePrecursorObjectList(ListView):
    model = Object
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(ReactivePrecursorObjectList, self).get_context_data(**kwargs)
        title = _("Reactive Precursor Objects Report")
        context.update(
            {
                "title_view": title,
                "report_urlnames": [
                    "reactive_precursor_object_list",
                    "reports_reactive_precursor_objects",
                ],
                "form": ReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "reactive_precursor",
                    }
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class LogObjectView(ReportListView):
    model = ObjectLogChange
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = _("Changes on Objects Report")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["object_change_logs"],
                "form": ObjectLogChangeBaseForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "report_objectschanges",
                    }
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class PrecursorsView(ReportListView):
    model = PrecursorReport
    template_name = "report/precursor_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_pk = self.kwargs["org_pk"]

        form = PrecursorFilterForm(self.request.GET or None, org_pk=org_pk)
        qs = PrecursorReport.objects.none()

        if not self.request.GET.get("laboratory"):
            default_lab = form.fields["laboratory"].queryset.first()
            if default_lab:
                form.initial["laboratory"] = default_lab
                qs = PrecursorReport.objects.filter(laboratory=default_lab).order_by(
                    "-pk"
                )

        elif form.is_valid():
            lab = form.cleaned_data["laboratory"]
            qs = PrecursorReport.objects.filter(laboratory=lab).order_by("-pk")

        context.update({"filter_form": form, "datalist": qs})
        return context

    def get_book(self, context):
        serializer = PrecursorSerializer(data=self.request.GET)
        book = []
        if serializer.is_valid():

            report = PrecursorReport.objects.get(pk=serializer.validated_data["pk"])
            month = report.get_month_display()
            laboratory = report.laboratory

            first_line = [
                _(
                    "Name of natural or legal person: %(lab)s  N° Registration: %(consecutive)d"
                )
                % {"lab": laboratory.name, "consecutive": report.consecutive}
            ]
            second_line = [
                _("Activity to which the company is dedicated: %(activity)s")
                % {"activity": ""}
            ]
            third_line = [
                _("Report of the Month:: %(month)s of the year: %(year)d Tel: %(tel)s")
                % {
                    "month": report.get_month_display(),
                    "year": report.year,
                    "tel": laboratory.phone_number,
                }
            ]
            fourth_line = [
                _(
                    "Responsible: %(responsible)s  Signature: %(signature)s  Position: %(position)s"
                )
                % {"responsible": "", "signature": "", "position": ""}
            ]
            range_data = [
                _("Period range of the data: %(date_range)s")
                % {"date_range": report.get_date_range()}
            ]

            book = [
                first_line,
                second_line,
                third_line,
                range_data,
                fourth_line,
                [],
                [
                    str(_("Name of the substance or product")),
                    str(_("Unit")),
                    str(_("Final balance of the previous report")),
                    str(_("Income during the month")),
                    str(
                        _(
                            "Import or local purchase invoice number that covers the entry"
                        )
                    ),
                    str(
                        _(
                            "Supplier that supplied the purchased product (in case of local purchase)"
                        )
                    ),
                    str(_("Total Stock")),
                    str(_("Dispatch or expense during this month")),
                    str(_("Balance at the end of the month reported in this report")),
                    str(_("Type of movement")),
                ],
            ]
            objects = PrecursorReportValues.objects.filter(precursor_report=report)
            for obj in objects.distinct().order_by("object__name"):
                resaon = obj.reason_to_spend if len(obj.reason_to_spend) > 0 else "N/A"
                book.append(
                    [
                        obj.object.name,
                        obj.measurement_unit.description,
                        obj.previous_balance,
                        obj.new_income,
                        obj.bills,
                        obj.providers,
                        obj.stock,
                        obj.month_expense,
                        obj.final_balance,
                        resaon,
                    ]
                )
            self.file_name = _("Report_of_precursors_%(month)s_%(consecutive)d") % {
                "consecutive": report.consecutive,
                "month": month,
            }
        return book


@method_decorator(permission_required("laboratory.do_report"), name="dispatch")
class DiscardShelfReportView(ListView):
    model = Shelf
    template_name = "report/base_report_form_view.html"

    def get_queryset(self):
        return Shelf.objects.none()

    def get_context_data(self, **kwargs):
        context = super(DiscardShelfReportView, self).get_context_data(**kwargs)
        title = _("Waste objects by shelf report")
        initial_data = {
            "name": slugify(title + " " + now().strftime("%x").replace("/", "-")),
            "title": title,
            "organization": self.org,
            "report_name": "report_waste_objects",
        }

        context.update(
            {
                "title_view": title,
                "form": DiscardShelfForm(initial=initial_data, org_pk=self.org),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class ReactiveReport(ListView):
    model = ShelfObject
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(ReactiveReport, self).get_context_data(**kwargs)
        title = _("Reactive Objects Report")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["reactive_report"],
                "form": ReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "reactive_report",
                    }
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class RiskZoneReport(ListView):
    model = RiskZone
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(RiskZoneReport, self).get_context_data(**kwargs)
        title = _("Risk Zone Report")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["risk_zone_report"],
                "form": RiskZoneReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "risk_zone_report",
                    },
                    org_pk=self.org,
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class ReactiveStockReport(ListView):
    model = ShelfObject
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(ReactiveStockReport, self).get_context_data(**kwargs)
        title = _("Reactive Stock Report")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["stock_reactive_report"],
                "form": ReactiveStockReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "stock_reactive_report",
                    }
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.do_report"), name="dispatch")
class FurnitureReportView(ListView):
    model = Furniture
    template_name = "report/base_report_form_view.html"

    def get_queryset(self):
        return Furniture.objects.filter(labroom__laboratory=self.lab)

    def get_context_data(self, **kwargs):
        context = super(FurnitureReportView, self).get_context_data(**kwargs)
        title = _("Objects by Furniture Report")
        initial_data = {
            "name": slugify(title + " " + now().strftime("%x").replace("/", "-")),
            "title": title,
            "organization": self.org,
            "report_name": "report_furniture",
        }

        if self.request.method == "GET":
            furniture_form = ValidateFurnitureForm(self.request.GET, org_pk=self.org)
            if furniture_form.is_valid():
                furniture = Furniture.objects.get(
                    pk=furniture_form.cleaned_data["furniture"]
                )
                initial_data.update(
                    {
                        "furniture": furniture,
                        "lab_room": furniture.labroom,
                    }
                )

        context.update(
            {
                "title_view": title,
                "report_urlnames": ["reports_furniture_detail"],
                "form": LaboratoryRoomReportForm(initial=initial_data, org_pk=self.org),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class CompatibilityReport(ListView):
    model = RiskZone
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(CompatibilityReport, self).get_context_data(**kwargs)
        title = _("SGA Compatibility Table")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["compatibility_report"],
                "form": CompatibilityReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "compatibility_report",
                    },
                    org_pk=self.org,
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class HazardMapReport(ListView):
    model = Laboratory
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super(HazardMapReport, self).get_context_data(**kwargs)
        title = _("Compatibility Laboratory")
        context.update(
            {
                "title_view": title,
                "report_urlnames": ["hazard_map_report"],
                "form": HazardMapReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "hazard_map_report",
                    },
                    org_pk=self.org,
                ),
            }
        )
        return context


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class PrecursorReportValuesView(ListView):
    model = PrecursorReportValues
    template_name = "report/precursor_report_values_view.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.precusor_pk = kwargs.get("precusor_pk")
        self.org_pk = kwargs.get("org_pk")

    def get_queryset(self):
        if self.precusor_pk:
            return PrecursorReportValues.objects.filter(pk=self.precusor_pk)
        return []

    def get_context_data(self, **kwargs):
        context = super(PrecursorReportValuesView, self).get_context_data(**kwargs)
        title = _("Precursor Report Values")
        context.update(
            {
                "title_view": title,
                "org_pk": self.org_pk,
                "precusor_pk": self.precusor_pk,
                "form_create": PrecursorReportValuesViewForm(
                    prefix="create",
                    render_type="as_grid",
                    precusor_pk=self.precusor_pk,
                    org_pk=self.org_pk,
                ),
                "form_update": PrecursorReportValuesViewForm(
                    prefix="update",
                    render_type="as_grid",
                    precusor_pk=self.precusor_pk,
                    org_pk=self.org_pk,
                ),
            }
        )
        return context
