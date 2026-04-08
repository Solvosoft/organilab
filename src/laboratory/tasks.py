from __future__ import absolute_import, unicode_literals

import importlib
import os
import re
import time
from collections import defaultdict
from datetime import date, timedelta

from async_notifications.utils import send_email_from_template
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import ProfilePermission
from laboratory.models import (
    Catalog,
    SDSTraceability,
    ShelfObject,
    SustanceCharacteristics,
    Laboratory,
    PrecursorReport,
    InformScheduler,
    Furniture,
    Object,
    ObjectMaximumLimit,
    BlockedListNotification,
    OrganizationStructure,
    OrganizationStructureRelations,
)
from pending_tasks.models import PendingTask
from pending_tasks.utils import create_pending_task
from .limit_shelfobject import send_email_limit_objs
from .task_utils import (
    create_informsperiods,
    save_object_report_precursor,
    build_precursor_report_from_reports,
)
from .utils_base_unit import get_conversion_units

app = importlib.import_module(settings.CELERY_MODULE).app
task_logger = get_task_logger(__name__)


def get_limited_shelf_objects(lab):
    return ShelfObject.objects.filter(
        in_where_laboratory=lab, limits__minimum_limit__isnull=False
    ).distinct()


@app.task
def notify_about_product_limit_reach():
    shelf_objects = ShelfObject.objects.filter(
        limits__isnull=False, in_where_laboratory__isnull=False
    ).select_related("object", "shelf__furniture__labroom")
    labs = Laboratory.objects.filter(
        pk__in=shelf_objects.values_list("in_where_laboratory", flat=True)
    ).distinct()
    object_list = {lab: [] for lab in labs}
    for shelfobjects in shelf_objects:
        if shelfobjects.quantity <= shelfobjects.limits.minimum_limit:
            object_list[shelfobjects.in_where_laboratory].append(shelfobjects)

    for lab in labs:
        if len(object_list[lab]) > 0 and lab.responsible:
            responsable = lab.responsible
            create_pending_task(
                responsable,
                _("List of ShelfObject in limits"),
                [],
                description=render_to_string(
                    "tasks/limit_shelfobject_notify.html",
                    {
                        "objects": object_list[lab],
                        "laboratory": lab,
                    },
                ),
                status=PendingTask.PENDING,
                profile=responsable.profile,
                link="",
                notify=True,
            )


@app.on_after_configure.connect
def setup_daily_tasks(sender, **kwargs):
    sender.add_periodic_task(2, notify_about_product_limit_reach.s(), name="notify")


@app.task()
def create_precursor_reports():
    day = date.today()

    for lab in Laboratory.objects.all():
        previos_report = PrecursorReport.objects.filter(laboratory=lab)

        if previos_report.exists():
            previos_report = previos_report.last()
        else:
            previos_report = None
        month_belong = day.month - 1
        if day.month == 1:
            month_belong = 12
        report = PrecursorReport.objects.create(
            month=day.month,
            year=day.year,
            laboratory=lab,
            consecutive=add_consecutive(lab),
            month_belong=month_belong,
        )
        save_object_report_precursor(report)
        build_precursor_report_from_reports(report, previos_report)


def add_consecutive(lab):
    report = PrecursorReport.objects.filter(laboratory=lab).last()
    consecutive = 1
    if report is not None:
        consecutive = int(report.consecutive) + 1

    return consecutive


@app.task
def create_informs_based_on_period():
    informschedulerquery = InformScheduler.objects.filter(active=True)
    for informscheduler in informschedulerquery:
        create_informsperiods(informscheduler)


@app.task()
def remove_shelf_not_furniture():
    furnitures = Furniture.objects.all()
    for furniture in furnitures:
        obj_pks = re.findall(r"\d+", furniture.dataconfig)
        furniture.shelf_set.all().exclude(pk__in=obj_pks).delete()


@app.task()
def add_maximum_object_stock_per_day():
    laboratories = Laboratory.objects.all()
    for laboratory in laboratories:
        objects = ShelfObject.objects.filter(
            in_where_laboratory=laboratory, object__type=Object.REACTIVE
        ).values_list("object", flat=True)
        objects = set(objects)
        for obj in Object.objects.filter(pk__in=objects):
            total = sum(
                [
                    get_conversion_units(
                        shelfobject.measurement_unit, shelfobject.quantity
                    )
                    for shelfobject in ShelfObject.objects.filter(
                        in_where_laboratory=laboratory, object=obj
                    )
                ]
            )
            shelfobject = ShelfObject.objects.filter(
                in_where_laboratory=laboratory, object=obj
            ).first()
            data = {
                "quantity": total,
                "laboratory": laboratory,
                "object": obj,
            }
            if shelfobject:
                data["measurement_unit"] = shelfobject.measurement_unit
            ObjectMaximumLimit.objects.create(**data)


@app.task()
def send_expiration_email():
    tomorrow = date.today() + timedelta(days=1)
    expiring_reactives = ShelfObject.objects.filter(
        object__type=Object.REACTIVE, reactive_expiration_date=tomorrow
    ).select_related("object", "shelf__furniture__labroom")
    reactives_by_lab = defaultdict(list)

    for reactive in expiring_reactives:
        lab = reactive.in_where_laboratory
        if lab:
            reactives_by_lab[lab].append(reactive)

    for lab in reactives_by_lab.keys():
        if lab.responsible:
            create_pending_task(
                lab.responsible,
                _("ShelfObject expiration"),
                [],
                description=render_to_string(
                    "tasks/expiration_shelfobject_notify.html",
                    {
                        "objects": reactives_by_lab[lab],
                        "laboratory": lab,
                        "date": tomorrow,
                    },
                ),
                status=PendingTask.PENDING,
                profile=lab.responsible.profile,
                link="",
                notify=True,
            )
        else:
            continue


@app.task()
def remove_relation_organization_laboratory():
    # remove relations of laboratories if not exists
    relations = OrganizationStructureRelations.objects.filter(
        content_type__app_label="laboratory",
        content_type__model="laboratory",
    )
    for relation in relations:
        lab = Laboratory.objects.filter(pk=relation.object_id).first()
        if not lab:
            relation.delete()

    # remove relations of organizations if not exists
    relations = OrganizationStructureRelations.objects.filter(
        content_type__app_label="laboratory",
        content_type__model="organizationstructure",
    )
    for relation in relations:
        org = OrganizationStructure.objects.filter(pk=relation.object_id).first()
        if not org:
            relation.delete()


def _get_sources_for_substance(sc, force_pubchem_replacement):
    """Determine which SDS sources to use and whether to force update.

    Returns (sources, force) tuple.
    """
    from laboratory.sds_sources import get_sources

    is_pubchem = SDSTraceability.objects.filter(
        sustance_characteristics=sc, source="pubchem"
    ).exists()

    if force_pubchem_replacement and is_pubchem:
        sources = get_sources(["merck"])
        return sources, True

    return get_sources(), False


def _resolve_pdf_path(sc):
    """Resolve the PDF path for a SustanceCharacteristics in MEDIA_ROOT."""
    if not sc.security_sheet or not sc.security_sheet.name:
        return None
    local_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
    if os.path.exists(local_path):
        return local_path
    return None


def _update_substance_from_pdf(sc):
    """Extract data from the SDS PDF and update substance fields.

    Uses .set() for h_codes and M2M catalog fields to replace completely.
    Returns (success, message) tuple.
    """
    from laboratory.utils_pdf import extract_msds_data, extract_catalog_fields
    from sga.models import DangerIndication

    file_path = _resolve_pdf_path(sc)
    if not file_path:
        return False, "no PDF file"

    data = extract_msds_data(file_path)
    if data is None:
        return False, "failed to extract PDF data"

    pdf_text = data.pop("_text", "")
    lang = data.get("_lang", "es")

    # Update simple fields (only if extracted value is not None)
    simple_fields = {
        "molecular_formula": data.get("molecular_formula"),
        "density": data.get("density"),
        "bioaccumulable": data.get("bioaccumulable"),
        "seveso_list": data.get("seveso_list"),
        "is_precursor": data.get("is_precursor"),
    }
    for field, value in simple_fields.items():
        if value is not None:
            setattr(sc, field, value)
    sc.save()

    # H-codes: SET (replace) instead of ADD
    h_codes = data.get("h_codes", [])
    if h_codes:
        h_code_objects = list(DangerIndication.objects.filter(code__in=h_codes))
        sc.h_code.set(h_code_objects)

    # Catalog fields
    catalog_keys = [
        "IARC",
        "IDMG",
        "white_organ",
        "ue_code",
        "nfpa",
        "storage_class",
        "Precursor",
    ]
    catalog_data = {}
    for key in catalog_keys:
        catalog_data[key] = list(
            Catalog.objects.filter(key=key)
            .order_by("pk")
            .values_list("pk", "description")
        )
    catalog_fields = (
        extract_catalog_fields(pdf_text, catalog_data, lang) if pdf_text else {}
    )

    # FK catalog fields
    for cat_key, model_field in [
        ("iarc", "iarc_id"),
        ("imdg", "imdg_id"),
        ("precursor_type", "precursor_type_id"),
    ]:
        value = catalog_fields.get(cat_key)
        if value is not None:
            setattr(sc, model_field, value)

    # M2M catalog fields: SET (replace)
    for field_name in ["white_organ", "ue_code", "nfpa", "storage_class"]:
        pks = catalog_fields.get(field_name, [])
        if pks:
            getattr(sc, field_name).set(pks)

    sc.save()
    return True, "updated"


@app.task()
def update_sds_and_extract_data(
    sc_ids=None, force_pubchem_replacement=True, max_years=5, delay=2
):
    """Celery task to update SDS documents and extract substance data.

    For each substance:
    1. Download/update SDS (replace PubChem with Merck when possible)
    2. Extract data from the PDF and update substance fields
    3. H-codes are set (replaced) exactly as found in the PDF

    Args:
        sc_ids: list of SustanceCharacteristics PKs (None = all with CAS)
        force_pubchem_replacement: if True, try Merck for PubChem SDSs
        max_years: max age before considering SDS outdated
        delay: seconds between downloads (rate limiting)
    """
    from laboratory.sds_sources import check_needs_update, update_sds_for_substance

    qs = (
        SustanceCharacteristics.objects.filter(cas_id_number__isnull=False)
        .exclude(cas_id_number="")
        .select_related("obj")
    )
    if sc_ids:
        qs = qs.filter(pk__in=sc_ids)

    total = qs.count()
    updated = 0
    skipped = 0
    errors = 0

    task_logger.info("Starting SDS update for %d substances", total)

    for i, sc in enumerate(qs.iterator(), 1):
        name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
        cas = sc.cas_id_number.strip()
        task_logger.info("[%d/%d] Processing %s (CAS: %s)", i, total, name, cas)

        try:
            # Determine if SDS needs downloading/updating
            sources, force = _get_sources_for_substance(sc, force_pubchem_replacement)
            needs_download = False
            file_path = _resolve_pdf_path(sc)

            if file_path is None:
                needs_download = True
            elif force:
                needs_download = True
            else:
                needs_update, _ = check_needs_update(file_path, max_years)
                needs_download = needs_update

            if needs_download:
                existing_pdf_path = _resolve_pdf_path(sc)
                sds_result = update_sds_for_substance(
                    sc,
                    sources=sources,
                    max_years=max_years,
                    force=force,
                    existing_pdf_path=existing_pdf_path,
                )
                if sds_result["status"] == "updated":
                    task_logger.info(
                        "[SDS] %s: downloaded from %s", name, sds_result["source"]
                    )
                    sc.refresh_from_db()
                elif sds_result["status"] == "no_source":
                    task_logger.warning("[SDS] %s: no source could provide SDS", name)
                elif sds_result["status"] == "error":
                    task_logger.warning(
                        "[SDS] %s: %s", name, sds_result.get("error", "unknown")
                    )

                if delay > 0:
                    time.sleep(delay)

            # Extract data from the PDF and update substance fields
            success, msg = _update_substance_from_pdf(sc)
            if success:
                task_logger.info("[OK] %s: %s", name, msg)
                updated += 1
            else:
                task_logger.warning("[SKIP] %s: %s", name, msg)
                skipped += 1

        except Exception as e:
            task_logger.error("[ERROR] %s: %s", name, e, exc_info=True)
            errors += 1

    task_logger.info(
        "SDS update complete. Processed: %d, Updated: %d, Skipped: %d, Errors: %d",
        total,
        updated,
        skipped,
        errors,
    )
    return {
        "total": total,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
