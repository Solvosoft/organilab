# encoding: utf-8
"""
Created on 26/12/2016

@author: luisza
"""
import math

import django_excel
from django.conf import settings
from django.contrib.auth.decorators import permission_required, login_required
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
    UserOrganization,
)

from laboratory.views.djgeneric import ListView, ReportListView
from laboratory.views.laboratory_utils import filter_by_user_and_hcode
from report.forms import (
    ReportForm,
    OrganizationReactiveForm,
)


@login_required
@permission_required("laboratory.do_report", raise_exception=True)
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


@login_required
@permission_required("laboratory.do_report", raise_exception=True)
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


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("laboratory.view_report", raise_exception=True),
    name="dispatch",
)
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


@login_required
@permission_required("laboratory.view_report", raise_exception=True)
def report_index(request, org_pk):

    user_perms = UserOrganization.objects.filter(
        organization=org_pk, user=request.user
    ).first()

    if not user_perms:
        raise Http404

    org = OrganizationStructure.objects.filter(pk=org_pk).first()
    if not org:
        raise Http404

    context = {"organization": org, "org_pk": org_pk}
    return render(request, "laboratory/reports/report_index.html", context=context)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("laboratory.view_report", raise_exception=True),
    name="dispatch",
)
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


def _donut_arc_path(cx, cy, r_outer, r_inner, start_angle, end_angle):
    """Return SVG path 'd' attribute for a donut arc segment."""
    sa = math.radians(start_angle - 90)
    ea = math.radians(end_angle - 90)
    x1_o = cx + r_outer * math.cos(sa)
    y1_o = cy + r_outer * math.sin(sa)
    x2_o = cx + r_outer * math.cos(ea)
    y2_o = cy + r_outer * math.sin(ea)
    x1_i = cx + r_inner * math.cos(ea)
    y1_i = cy + r_inner * math.sin(ea)
    x2_i = cx + r_inner * math.cos(sa)
    y2_i = cy + r_inner * math.sin(sa)
    large_arc = 1 if (end_angle - start_angle) > 180 else 0
    return (
        f"M {x1_o:.2f},{y1_o:.2f} "
        f"A {r_outer},{r_outer} 0 {large_arc} 1 {x2_o:.2f},{y2_o:.2f} "
        f"L {x1_i:.2f},{y1_i:.2f} "
        f"A {r_inner},{r_inner} 0 {large_arc} 0 {x2_i:.2f},{y2_i:.2f} Z"
    )


@login_required
def sds_coverage_svg(request, org_pk):
    from laboratory.models import SustanceCharacteristics, SDSTraceability
    from django.db.models import Subquery, OuterRef

    qs = SustanceCharacteristics.objects.filter(obj__organization__pk=org_pk)
    total = qs.count()

    if total == 0:
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="100">'
            '<text x="300" y="50" text-anchor="middle" font-family="sans-serif" '
            'font-size="16" fill="#666">No hay sustancias registradas</text></svg>'
        )
        return HttpResponse(svg, content_type="image/svg+xml")

    # Get latest traceability source per substance
    latest_trace = SDSTraceability.objects.filter(
        sustance_characteristics=OuterRef("pk")
    ).order_by("-creation_date")

    annotated = qs.annotate(latest_source=Subquery(latest_trace.values("source")[:1]))

    source_counts = {}
    no_sds_count = 0
    for row in annotated.values_list("latest_source", flat=True):
        if row is None:
            no_sds_count += 1
        else:
            source_counts[row] = source_counts.get(row, 0) + 1

    SOURCE_COLORS = {
        "merck": "#E59E40",
        "pubchem": "#00A896",
        "fisher": "#CF82B6",
        "panreac": "#0280A0",
        "carlo_erba": "#F07060",
        "jt_baker": "#A597C3",
        "honeywell": "#A1B2C8",
        "unknown": "#F5D890",
        "manual": "#99EBA8",
    }
    NO_SDS_COLOR = "#D9D9D9"
    SOURCE_LABELS = dict(SDSTraceability.SDS_SOURCE_CHOICES)

    segments = []
    for source_key, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        label = str(SOURCE_LABELS.get(source_key, source_key))
        color = SOURCE_COLORS.get(source_key, "#BBBBBB")
        segments.append((label, count, color))
    if no_sds_count > 0:
        segments.append((str(_("Sin FDS")), no_sds_count, NO_SDS_COLOR))

    with_sds = total - no_sds_count
    coverage_pct = (with_sds / total * 100) if total else 0

    # SVG layout
    svg_w = 700
    cx, cy = 200, 200
    r_outer, r_inner = 140, 80
    legend_x = 380

    legend_h = max(len(segments) * 24, 0)
    table_y = max(cy + r_outer + 80, legend_h + 120)
    row_h = 28
    table_rows = len(segments) + 2
    svg_h = table_y + table_rows * row_h + 20

    parts = []
    parts.append(
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )
    parts.append(
        "<style>"
        'text { font-family: "Segoe UI", Arial, sans-serif; }'
        ".title { font-size: 18px; font-weight: bold; fill: #333; }"
        ".center-pct { font-size: 28px; font-weight: bold; fill: #333; }"
        ".center-label { font-size: 12px; fill: #666; }"
        ".legend-text { font-size: 13px; fill: #333; }"
        ".table-header { font-size: 12px; font-weight: bold; fill: #fff; }"
        ".table-cell { font-size: 12px; fill: #333; }"
        ".table-total { font-size: 12px; font-weight: bold; fill: #333; }"
        "</style>"
    )

    parts.append(
        f'<text x="{svg_w // 2}" y="30" text-anchor="middle" class="title">'
        f"Cobertura FDS</text>"
    )

    # Donut chart
    donut_cy = cy + 40
    if len(segments) == 1:
        parts.append(
            f'<circle cx="{cx}" cy="{donut_cy}" r="{r_outer}" fill="{segments[0][2]}" />'
        )
        parts.append(f'<circle cx="{cx}" cy="{donut_cy}" r="{r_inner}" fill="white" />')
    else:
        angle = 0
        for _label, count, color in segments:
            sweep = count / total * 360
            if sweep <= 0:
                continue
            end_angle = angle + min(sweep, 359.99)
            d = _donut_arc_path(cx, donut_cy, r_outer, r_inner, angle, end_angle)
            parts.append(
                f'<path d="{d}" fill="{color}" stroke="white" stroke-width="1.5" />'
            )
            angle += sweep

    # Center text
    parts.append(
        f'<text x="{cx}" y="{donut_cy - 5}" text-anchor="middle" class="center-pct">'
        f"{coverage_pct:.0f}%</text>"
    )
    parts.append(
        f'<text x="{cx}" y="{donut_cy + 15}" text-anchor="middle" class="center-label">'
        f"con SDS</text>"
    )

    # Legend
    ly = 100
    for label, count, color in segments:
        parts.append(
            f'<rect x="{legend_x}" y="{ly - 10}" width="14" height="14" rx="2" fill="{color}" />'
        )
        parts.append(
            f'<text x="{legend_x + 20}" y="{ly + 2}" class="legend-text">'
            f"{label} ({count})</text>"
        )
        ly += 24

    # Summary table
    col_widths = [200, 100, 100]
    table_x = 100
    total_w = sum(col_widths)

    parts.append(
        f'<rect x="{table_x}" y="{table_y}" width="{total_w}" '
        f'height="{row_h}" rx="4" fill="#4a90a4" />'
    )
    headers = [str(_("Fuente")), str(_("Cantidad")), str(_("Porcentaje"))]
    hx = table_x
    for i, header in enumerate(headers):
        parts.append(
            f'<text x="{hx + col_widths[i] // 2}" y="{table_y + 18}" '
            f'text-anchor="middle" class="table-header">{header}</text>'
        )
        hx += col_widths[i]

    ry = table_y + row_h
    for idx, (label, count, color) in enumerate(segments):
        bg = "#f8f8f8" if idx % 2 == 0 else "#ffffff"
        parts.append(
            f'<rect x="{table_x}" y="{ry}" width="{total_w}" height="{row_h}" fill="{bg}" />'
        )
        parts.append(
            f'<rect x="{table_x + 8}" y="{ry + 7}" width="12" height="12" rx="2" fill="{color}" />'
        )
        parts.append(
            f'<text x="{table_x + 26}" y="{ry + 18}" class="table-cell">{label}</text>'
        )
        parts.append(
            f'<text x="{table_x + col_widths[0] + col_widths[1] // 2}" y="{ry + 18}" '
            f'text-anchor="middle" class="table-cell">{count}</text>'
        )
        pct = count / total * 100 if total else 0
        parts.append(
            f'<text x="{table_x + col_widths[0] + col_widths[1] + col_widths[2] // 2}" '
            f'y="{ry + 18}" text-anchor="middle" class="table-cell">{pct:.1f}%</text>'
        )
        ry += row_h

    # Total row
    parts.append(
        f'<rect x="{table_x}" y="{ry}" width="{total_w}" height="{row_h}" fill="#e8e8e8" />'
    )
    parts.append(
        f'<text x="{table_x + 10}" y="{ry + 18}" class="table-total">Total</text>'
    )
    parts.append(
        f'<text x="{table_x + col_widths[0] + col_widths[1] // 2}" y="{ry + 18}" '
        f'text-anchor="middle" class="table-total">{total}</text>'
    )
    parts.append(
        f'<text x="{table_x + col_widths[0] + col_widths[1] + col_widths[2] // 2}" '
        f'y="{ry + 18}" text-anchor="middle" class="table-total">100%</text>'
    )

    # Table border
    table_total_h = row_h * (len(segments) + 2)
    parts.append(
        f'<rect x="{table_x}" y="{table_y}" width="{total_w}" '
        f'height="{table_total_h}" rx="4" fill="none" stroke="#ddd" stroke-width="1" />'
    )

    parts.append("</svg>")
    svg_content = "\n".join(parts)
    return HttpResponse(svg_content, content_type="image/svg+xml")
