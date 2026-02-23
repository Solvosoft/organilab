# encoding: utf-8
"""
Created on 26/12/2016

@author: luisza
"""
import django_excel
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from weasyprint import HTML

from laboratory.forms import H_CodeForm
from laboratory.models import (
    ShelfObject,
    OrganizationStructure,
)

from laboratory.views.djgeneric import ListView, ReportListView
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from report.forms import (
    ReportForm,
    OrganizationReactiveForm,
)


@permission_required("laboratory.do_report")
def report_shelf_objects(request, org_pk, lab_pk, pk):

    if not pk:
        if lab_pk:
            shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=lab_pk
            )
        else:
            shelf_objects = ShelfObject.objects.all()
    else:
        shelf_objects = ShelfObject.objects.filter(pk=pk)

    context = {
        "user": request.user,
        "title": "Shelf Object Report",
        "verbose_name": "Organilab Shelf Objects Report",
        "object_list": shelf_objects,
        "datetime": timezone.now(),
        "request": request,
        "org_pk": org_pk,
        "laboratory": lab_pk,
        "domain": "file://%s" % (str(settings.MEDIA_ROOT).replace("/media/", ""),),
    }

    template = get_template("pdf/shelf_object_pdf.html")

    html = template.render(context=context)
    page = HTML(
        string=html, encoding="utf-8", base_url=request.build_absolute_uri()
    ).write_pdf()

    response = HttpResponse(page, content_type="application/pdf")

    response["Content-Disposition"] = 'attachment; filename="report_shelf_objects.pdf"'
    return response


@permission_required("laboratory.do_report")
def report_h_code(request, *args, **kwargs):
    form = H_CodeForm(request.GET)
    q = []
    if form.is_valid():
        q = form.cleaned_data["hcode"]
    fileformat = request.GET.get("format", "pdf")
    if fileformat in ["xls", "xlsx", "ods"]:
        object_list = filter_by_user_and_hcode(
            request.user, q, function="convert_hcodereport_list"
        )
        return django_excel.make_response_from_array(
            object_list, fileformat, file_name="hcode_report.%s" % (fileformat,)
        )
    else:
        object_list = filter_by_user_and_hcode(
            request.user, q, function="convert_hcodereport_table"
        )

    template = get_template("pdf/hcode_pdf.html")

    context = {
        "verbose_name": "H code report",
        "object_list": object_list,
        "datetime": timezone.now(),
        "request": request,
    }

    html = template.render(context=context)
    page = HTML(string=html, encoding="utf-8").write_pdf()

    response = HttpResponse(page, content_type="application/pdf")

    response["Content-Disposition"] = 'attachment; filename="hcode_report.pdf"'

    return response


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class OrganizationReactivePresenceList(ReportListView):
    model = OrganizationStructure
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = _("Occupational Health Report")
        context.update(
            {
                "title_view": title,
                "laboratory": 0,
                "report_urlnames": ["organizationreactivepresence"],
                "form": OrganizationReactiveForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "report_organization_reactive_list",
                    },
                    org_pk=self.org,
                ),
            }
        )
        return context


def getLevelClass(level):
    color = {
        0: "default",
        1: "danger",
        2: "info",
        3: "warning",
        4: "default",
        5: "danger",
        6: "info",
    }
    level = level % 6
    cl = "col-md-12"
    if level:
        cl = "col-md-%d offset-md-%d" % (12 - level, level)
    return cl, color[level]


@permission_required("laboratory.view_report")
def report_index(request, org_pk):
    org = (
        OrganizationStructure.os_manager.filter_user(request.user)
        .filter(pk=org_pk)
        .first()
    )
    if not org:
        raise Http404

    context = {"organization": org, "org_pk": org_pk}
    return render(request, "laboratory/reports/report_index.html", context=context)


@method_decorator(permission_required("laboratory.view_report"), name="dispatch")
class ChemicalInventoryReport(ReportListView):
    model = ShelfObject
    template_name = "report/base_report_form_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = _("Chemical inventory report")
        context.update(
            {
                "title_view": title,
                "laboratory": 0,
                "report_urlnames": ["chemicalinventory"],
                "form": ReportForm(
                    initial={
                        "name": slugify(
                            title + " " + now().strftime("%x").replace("/", "-")
                        ),
                        "title": title,
                        "organization": self.org,
                        "report_name": "chemicalinventory",
                    },
                    org_pk=self.org,
                ),
            }
        )
        return context
