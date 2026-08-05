import json
import logging
import os
import zipfile
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls.base import reverse
from django.utils.translation import gettext as _

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import (
    Catalog,
    Object,
    OrganizationStructure,
    SDSTraceability,
)
from laboratory.utils_pdf import extract_catalog_fields, extract_msds_data
from msds.forms import SDSUploadForm, SDSConfirmForm
from msds.models import RegulationDocument
from sga.models import DangerIndication, SubstanceCharacteristics

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
    objs = SDSTraceability.objects.filter(
        sga_substance_characteristics__object_related__organization__pk=org_pk
    ).select_related("sga_substance_characteristics__object_related")

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
    context = {"org_pk": org_pk}

    if request.method == "POST" and "confirm" in request.POST:
        return _sds_create_confirm(request, org_pk, context)

    if request.method == "POST":
        return _sds_create_upload(request, org_pk, context)

    # GET — step 1: upload form
    context["step"] = 1
    context["upload_form"] = SDSUploadForm()
    return render(request, "msds/sds_create.html", context)


def _build_catalog_dict():
    """Build the catalogs dict expected by extract_catalog_fields."""
    catalog_keys = [
        "IARC",
        "IDMG",
        "white_organ",
        "ue_code",
        "nfpa",
        "storage_class",
        "Precursor",
    ]
    catalogs = {}
    for key in catalog_keys:
        catalogs[key] = list(
            Catalog.objects.filter(key=key).values_list("pk", "description")
        )
    return catalogs


def _sds_create_upload(request, org_pk, context):
    upload_form = SDSUploadForm(request.POST, request.FILES)
    if not upload_form.is_valid():
        context["step"] = 1
        context["upload_form"] = upload_form
        return render(request, "msds/sds_create.html", context)

    uploaded_file = request.FILES["file"]
    temp_name = "tmp/sds/%s.pdf" % uuid4()
    saved_name = default_storage.save(temp_name, uploaded_file)
    full_path = default_storage.path(saved_name)

    extracted = extract_msds_data(full_path)
    if extracted is None:
        extracted = {}
        messages.warning(
            request,
            _(
                "Could not extract data from the PDF. Please fill in the fields manually."
            ),
        )

    h_codes = extracted.get("h_codes", [])
    text = extracted.get("_text", "")
    request.session["sds_temp_file"] = saved_name

    # Extract catalog fields from PDF text
    catalog_fields = {}
    if text:
        catalogs = _build_catalog_dict()
        catalog_fields = extract_catalog_fields(
            text, catalogs, extracted.get("_lang", "es")
        )

    # Pre-select h_code DangerIndication objects by code
    h_code_pks = list(
        DangerIndication.objects.filter(code__in=h_codes).values_list("pk", flat=True)
    )

    revision_date = extracted.get("revision_date")

    initial = {
        "name": extracted.get("product_name", ""),
        "cas_id_number": extracted.get("cas_id_number", ""),
        "molecular_formula": extracted.get("molecular_formula", ""),
        "density": extracted.get("density"),
        "bioaccumulable": extracted.get("bioaccumulable"),
        "is_precursor": extracted.get("is_precursor", False),
        "seveso_list": extracted.get("seveso_list", False),
        "revision_date": revision_date,
        # Catalog FK fields (single PK or None)
        "iarc": catalog_fields.get("iarc"),
        "imdg": catalog_fields.get("imdg"),
        "precursor_type": catalog_fields.get("precursor_type"),
        # Catalog M2M fields (lists of PKs)
        "h_code": h_code_pks,
        "white_organ": catalog_fields.get("white_organ", []),
        "ue_code": catalog_fields.get("ue_code", []),
        "nfpa": catalog_fields.get("nfpa", []),
        "storage_class": catalog_fields.get("storage_class", []),
    }

    context["step"] = 2
    context["confirm_form"] = SDSConfirmForm(initial=initial)
    return render(request, "msds/sds_create.html", context)


def _sds_create_confirm(request, org_pk, context):
    confirm_form = SDSConfirmForm(request.POST)
    if not confirm_form.is_valid():
        context["step"] = 2
        context["confirm_form"] = confirm_form
        return render(request, "msds/sds_create.html", context)

    temp_file_name = request.session.get("sds_temp_file")

    if not temp_file_name or not default_storage.exists(temp_file_name):
        messages.error(request, _("Temporary file not found. Please upload again."))
        context["step"] = 1
        context["upload_form"] = SDSUploadForm()
        return render(request, "msds/sds_create.html", context)

    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    cd = confirm_form.cleaned_data

    obj = Object(
        name=cd["name"],
        type=Object.REACTIVE,
        organization=organization,
        created_by=request.user,
    )
    obj.save()

    full_path = default_storage.path(temp_file_name)
    file_name = "%s.pdf" % (cd.get("cas_id_number") or obj.pk)

    sc = SubstanceCharacteristics(
        object_related=obj,
        cas_id_number=cd.get("cas_id_number") or None,
        molecular_formula=cd.get("molecular_formula") or None,
        density=cd.get("density") or 0,
        bioaccumulable=cd.get("bioaccumulable"),
        is_precursor=cd.get("is_precursor", False),
        seveso_list=cd.get("seveso_list", False),
        iarc=cd.get("iarc"),
        imdg=cd.get("imdg"),
        precursor_type=cd.get("precursor_type"),
    )
    with open(full_path, "rb") as f:
        sc.security_sheet.save(file_name, File(f), save=False)
    sc.save()

    # M2M fields
    if cd.get("h_code"):
        sc.h_code.set(cd["h_code"])
    if cd.get("white_organ"):
        sc.white_organ.set(cd["white_organ"])
    if cd.get("ue_code"):
        sc.ue_code.set(cd["ue_code"])
    if cd.get("nfpa"):
        sc.nfpa.set(cd["nfpa"])
    if cd.get("storage_class"):
        sc.storage_class.set(cd["storage_class"])

    trace = SDSTraceability(
        sga_substance_characteristics=sc,
        source="manual",
        revision_date=cd.get("revision_date"),
        created_by=request.user,
    )
    with open(full_path, "rb") as f:
        trace.security_sheet.save(file_name, File(f), save=False)
    trace.save()

    # Clean up temp file and session
    default_storage.delete(temp_file_name)
    request.session.pop("sds_temp_file", None)

    messages.success(request, _("SDS uploaded and substance created successfully"))
    return HttpResponseRedirect(reverse("msds:index_msds", kwargs={"org_pk": org_pk}))


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
@permission_required("laboratory.view_sdstraceability", raise_exception=True)
def verified_sds(request, org_pk):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    return render(request, "msds/verified_sds.html", context={"org_pk": org_pk})
