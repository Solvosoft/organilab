import logging
import os
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile

from .merck import MerckSource
from .pubchem import PubChemSource

logger = logging.getLogger("organilab")

SOURCES = {
    "merck": MerckSource,
}

SOURCE_NAME_TO_KEY = {
    "Merck": "merck",
    "Sigma-Aldrich": "merck",
    "Fisher/Thermo": "fisher",
    "Panreac": "panreac",
    "Carlo Erba": "carlo_erba",
    "JT Baker": "jt_baker",
    "PubChem": "pubchem",
    "Honeywell": "honeywell",
    "Sin identificar": "unknown",
}


def get_sources(source_names=None):
    """Return a list of SDSSource instances filtered by name."""
    if source_names is None or source_names == ["all"]:
        return [cls() for cls in SOURCES.values()]
    return [SOURCES[name]() for name in source_names if name in SOURCES]


def check_needs_update(pdf_path, max_years=5):
    """Check if a PDF needs updating based on its revision date.

    Returns (needs_update: bool, revision_date: str).
    needs_update is True if the date is older than max_years or cannot be determined.
    """
    from laboratory.management.commands.identify_sds_sources import (
        _extract_revision_date,
        _extract_text,
        _needs_update,
    )

    text = _extract_text(pdf_path)
    if not text.strip():
        return True, ""

    revision_date = _extract_revision_date(text)
    status = _needs_update(revision_date, max_years)
    return status != "no", revision_date


def update_sds_for_substance(
    sc, sources=None, max_years=5, dry_run=False, force=False, existing_pdf_path=None
):
    """Try to update the SDS for a SustanceCharacteristics instance.

    Args:
        sc: SustanceCharacteristics instance (with obj relation loaded)
        sources: list of SDSSource instances to try (in order)
        max_years: max age in years before considering SDS outdated
        dry_run: if True, only check without downloading
        force: if True, update even if current SDS is not expired
        existing_pdf_path: optional path to an existing PDF to pass to sources
            for metadata extraction

    Returns:
        dict with keys: status, source, old_date, error
        status: 'updated', 'skipped', 'no_source', 'error', 'dry_run'
    """
    if sources is None:
        sources = get_sources()

    name = str(sc.obj) if sc.obj else f"PK={sc.pk}"
    cas = (sc.cas_id_number or "").strip()
    substance_name = str(sc.obj.name) if sc.obj else ""

    result = {
        "pk": sc.pk,
        "name": name,
        "cas": cas,
        "status": "skipped",
        "source": None,
        "old_date": "",
        "error": None,
    }

    if not cas:
        result["status"] = "error"
        result["error"] = "no CAS number"
        return result

    # Check if current SDS needs update
    if not force and sc.security_sheet:
        full_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
        if os.path.exists(full_path):
            needs_update, revision_date = check_needs_update(full_path, max_years)
            result["old_date"] = revision_date
            if not needs_update:
                result["status"] = "skipped"
                return result

    if dry_run:
        result["status"] = "dry_run"
        return result

    # Resolve existing PDF path for sources that can extract metadata
    if existing_pdf_path is None and sc.security_sheet:
        candidate = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
        if os.path.exists(candidate):
            existing_pdf_path = candidate

    # Try each source in order
    for source in sources:
        try:
            search_result = source.search(
                cas, substance_name, pdf_path=existing_pdf_path
            )
            if not search_result:
                logger.info("[%s] No results for %s (CAS: %s)", source.name, name, cas)
                continue

            # Download to temp file first
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name

            success = source.download(search_result, tmp_path)
            if not success:
                logger.info(
                    "[%s] Download failed for %s (CAS: %s)", source.name, name, cas
                )
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                continue

            # Delete old file from disk
            old_sheet_name = sc.security_sheet.name if sc.security_sheet else None
            if old_sheet_name:
                old_path = os.path.join(settings.MEDIA_ROOT, old_sheet_name)
                if os.path.exists(old_path):
                    os.remove(old_path)
                    logger.info("Deleted old SDS from MEDIA_ROOT: %s", old_path)

            # Save new file to the model
            from laboratory.models_utils import upload_files

            with open(tmp_path, "rb") as f:
                content = f.read()
            filename = f"sds_{cas.replace('-', '_')}.pdf"
            sc.security_sheet.save(filename, ContentFile(content), save=True)

            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            result["status"] = "updated"
            result["source"] = source.name
            logger.info("[%s] Updated SDS for %s (CAS: %s)", source.name, name, cas)

            # Create traceability record
            try:
                from laboratory.models import SDSTraceability
                from laboratory.management.commands.identify_sds_sources import (
                    _extract_revision_date,
                    _extract_text,
                    _parse_date,
                )

                rev_date = None
                # First try to get date from search_result metadata (e.g. PubChem provides 'retrieved')
                retrieved = (search_result.get("metadata") or {}).get("retrieved", "")
                if retrieved:
                    rev_date = _parse_date(retrieved)

                # Fall back to PDF text extraction
                if rev_date is None:
                    new_path = os.path.join(settings.MEDIA_ROOT, sc.security_sheet.name)
                    text = _extract_text(new_path)
                    rev_date_str = _extract_revision_date(text)
                    rev_date = _parse_date(rev_date_str)

                SDSTraceability.objects.update_or_create(
                    sga_substance_characteristics=sc,
                    defaults={
                        "source": source.name,
                        "revision_date": rev_date,
                        "download_url": search_result.get("url", "") or "",
                    },
                )
            except Exception as e:
                logger.warning(
                    "Could not create SDS traceability record for %s: %s", name, e
                )

            return result

        except Exception as e:
            logger.warning("[%s] Error updating %s: %s", source.name, name, e)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            continue

    result["status"] = "no_source"
    result["error"] = "no source could provide an SDS"
    return result
