import json
import logging
import os
import zipfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls.base import reverse
from django.utils.translation import gettext as _

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from msds.models import RegulationDocument
from sga.models import SDSTraceability

logger = logging.getLogger("organilab")


@login_required
@permission_required("msds.view_msdsobject", raise_exception=True)
def index_msds(request, org_pk):
    source_labels = dict(SDSTraceability.SDS_SOURCE_CHOICES)
    existing_sources = (
        SDSTraceability.objects.filter(
            sga_substance_characteristics__object_related__organization__pk=org_pk
        )
        .order_by("source")
        .values_list("source", flat=True)
        .distinct()
    )
    source_choices = [
        [src, str(source_labels.get(src, src))] for src in existing_sources
    ]
    context = {
        "org_pk": org_pk,
        "source_choices_json": json.dumps(source_choices),
    }
    return render(request, "index_msds.html", context=context)


@login_required
@permission_required("msds.view_msdsobject", raise_exception=True)
def get_list_msds(request, org_pk):
    # La trazabilidad es un historial: una sustancia puede acumular varias fichas
    # a lo largo del tiempo. Esta pantalla busca sustancias, así que muestra solo
    # la vigente de cada una; el historial completo vive en «verified_sds».
    latest_per_substance = (
        SDSTraceability.objects.filter(
            sga_substance_characteristics=OuterRef("sga_substance_characteristics")
        )
        .order_by("-creation_date")
        .values("pk")[:1]
    )
    objs = (
        SDSTraceability.objects.filter(
            sga_substance_characteristics__object_related__organization__pk=org_pk
        )
        .filter(pk=Subquery(latest_per_substance))
        .select_related("sga_substance_characteristics__object_related")
    )

    records_total = objs.count()

    # Global search (DataTables search[value])
    q = request.GET.get("search[value]") or request.GET.get("q")
    if q:
        objs = objs.filter(
            Q(sga_substance_characteristics__object_related__name__icontains=q)
            | Q(sga_substance_characteristics__cas_id_number__icontains=q)
        )

    # Column filters (sent by formatDataTableParams)
    substance_filter = request.GET.get("substance__icontains") or request.GET.get(
        "substance"
    )
    if substance_filter:
        objs = objs.filter(
            sga_substance_characteristics__object_related__name__icontains=substance_filter
        )

    cas_filter = request.GET.get("cas_code__icontains") or request.GET.get("cas_code")
    if cas_filter:
        objs = objs.filter(
            sga_substance_characteristics__cas_id_number__icontains=cas_filter
        )

    source_filter = request.GET.get("source")
    if source_filter:
        objs = objs.filter(source=source_filter)

    revision_date_filter = request.GET.get("revision_date")
    if revision_date_filter and "," in revision_date_filter:
        dates = revision_date_filter.split(",")
        if len(dates) == 2:
            date_from, date_to = dates[0].strip(), dates[1].strip()
            if date_from:
                objs = objs.filter(revision_date__gte=date_from)
            if date_to:
                objs = objs.filter(revision_date__lte=date_to)

    objs = objs.order_by("-last_update")
    records_filtered = objs.count()

    # Pagination: support both DataTables native (start/length) and DRF (page/page_size)
    try:
        page_size = int(request.GET.get("page_size") or request.GET.get("length") or 25)
        page_num = request.GET.get("page")
        if page_num:
            page_num = int(page_num)
        else:
            start = int(request.GET.get("start", 0))
            page_num = 1 + (start // page_size)
    except (ValueError, ZeroDivisionError):
        page_size = 25
        page_num = 1

    p = Paginator(objs, page_size)
    if page_num > p.num_pages and p.num_pages > 0:
        page_num = 1
    page = (
        p.page(page_num)
        if p.num_pages > 0
        else (
            p.page(1)
            if records_filtered == 0 and p.num_pages == 0
            else p.page(page_num)
        )
    )

    data = []
    for trace in page.object_list:
        sc = trace.sga_substance_characteristics
        obj_name = sc.object_related.name if sc and sc.object_related else ""
        cas = sc.cas_id_number or "" if sc else ""
        source = trace.get_source_display()
        revision = str(trace.revision_date) if trace.revision_date else ""
        updated = str(trace.last_update.date()) if trace.last_update else ""

        sheet = trace.security_sheet or (sc.security_sheet if sc else None)
        if sheet:
            download = '<a href="%s" target="_blank">%s</a>' % (
                sheet.url,
                _("Download"),
            )
        else:
            download = "N/A"

        data.append([obj_name, cas, source, revision, updated, download])

    dev = {
        "data": data,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
    }

    draw = request.GET.get("draw") or request.GET.get("_")
    if draw:
        try:
            dev["draw"] = int(draw)
        except (ValueError, TypeError):
            pass
    return JsonResponse(dev)


@login_required
@permission_required("msds.add_msdsobject", raise_exception=True)
def sds_create(request, org_pk):
    """Redirige al asistente de sustancias de SGA.

    El alta de sustancias vive en un solo sitio, el asistente de SGA, que sube la
    ficha, encola su extracción y registra la trazabilidad. Mantener aquí un
    segundo camino obligaría a duplicar esa lógica y a que ambas versiones
    divergieran; la ruta se conserva para no romper enlaces guardados.
    """
    return HttpResponseRedirect(
        reverse("sga:create_sustance", kwargs={"org_pk": org_pk})
    )


def regulation_view(request):
    regulations = RegulationDocument.objects.all()
    return render(
        request, "regulation/regulations_document.html", {"object_list": regulations}
    )


def get_name(name, country, path):
    ext = path.split(".")[-1]
    return "%s_%s.%s" % (name, country, ext)


def download_all_regulations(request):
    response = HttpResponse(content_type="application/force-download")
    z = zipfile.ZipFile(response, "w")
    regulations = RegulationDocument.objects.all()
    for doc in regulations:
        doc.file.open("rb")
        name = get_name(doc.name, doc.country, doc.file.url)
        z.write(os.path.join(settings.MEDIA_ROOT, doc.file.path), name)
    for file in z.filelist:
        file.create_system = 0
    z.close()
    response["Content-Disposition"] = 'attachment; filename="regulations.zip"'
    return response


@login_required
@permission_required("sga.view_sdstraceability", raise_exception=True)
def verified_sds(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    return render(request, "msds/verified_sds.html", context={"org_pk": org_pk})
