"""Creación o actualización de equipos a partir de las filas revisadas del Excel.

La reimportación es idempotente: un equipo se reconoce por su código interno dentro del
laboratorio y se actualiza en lugar de duplicarse. Un valor vacío en el Excel nunca
borra lo que ya estaba registrado.
"""
import datetime

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils.translation import gettext as _

from auth_and_perms.models import Profile
from laboratory.equipment.importer import normalize_label
from laboratory.models import (
    Catalog,
    EquipmentActivityPlan,
    EquipmentCharacteristics,
    Object,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectMaintenance,
)

#: campo de la fila -> campo de la ficha (se copia solo si la fila trae valor)
TEXT_FIELDS = {
    "internal_code": "internal_code",
    "brand": "brand",
    "model": "model",
    "serial_number": "serial_number",
    "asset_number": "asset_number",
    "physical_location": "physical_location",
    "software_version": "software_version",
    "measurement_unit": "measurement_unit",
    "resolution": "resolution",
    "working_range": "working_range",
}


def initials(text):
    return "".join(word[0] for word in normalize_label(text).split() if word)


class ProfileMatcher:
    """Resuelve «Xindy Víquez R.» o «XVR» a un perfil de la organización.

    Un nombre o unas iniciales que corresponden a más de un perfil no se resuelven:
    se deja que la persona lo elija en la revisión.
    """

    def __init__(self, organization):
        self.by_name, self.by_initials = {}, {}
        profiles = Profile.objects.filter(user__in=organization.users.all()).select_related("user")
        for profile in profiles:
            full = " ".join(part for part in (profile.user.first_name, profile.user.last_name) if part)
            for key, index in ((normalize_label(full), self.by_name), (initials(full), self.by_initials)):
                if key:
                    index.setdefault(key, set()).add(profile.pk)
            username = normalize_label(profile.user.username)
            if username:
                self.by_name.setdefault(username, set()).add(profile.pk)

    def match(self, text):
        if not text:
            return None
        key = normalize_label(text)
        candidates = self.by_name.get(key) or self.by_initials.get(key.replace(" ", ""))
        if not candidates:
            # «Xindy Víquez R.»: el apellido abreviado no coincide letra a letra.
            candidates = {
                pk for name, pks in self.by_name.items() if name.startswith(key.rsplit(" ", 1)[0])
                for pk in pks
            } if " " in key else set()
        return next(iter(candidates)) if len(candidates) == 1 else None


def catalog_value(key, description):
    if not description:
        return None
    found = Catalog.objects.filter(key=key, description__iexact=description).first()
    return found or Catalog.objects.create(key=key, description=description)


def months_between(start, end):
    delta = relativedelta(end, start)
    return delta.years * 12 + delta.months


class EquipmentImporter:
    def __init__(self, organization, laboratory, shelf, user, request):
        self.organization = organization
        self.laboratory = laboratory
        self.shelf = shelf
        self.user = user
        self.request = request
        self.summary = {"created": 0, "updated": 0, "calibrations": 0, "maintenances": 0, "plans": 0}

    # -- equipo -------------------------------------------------------------------------
    def find(self, code):
        if not code:
            return None
        return (
            Characteristics.objects.filter(
                internal_code__iexact=code, shelfobject__in_where_laboratory=self.laboratory
            )
            .select_related("shelfobject")
            .first()
        )

    def catalog_object(self, name):
        organizations = self.organization.ancestors(include_self=True)
        obj = Object.objects.filter(
            type=Object.EQUIPMENT, name__iexact=name, organization__in=organizations
        ).first()
        if obj is None:
            obj = Object.objects.create(name=name, type=Object.EQUIPMENT, organization=self.organization)
        EquipmentCharacteristics.objects.get_or_create(object=obj)
        return obj

    def create_unit(self, row):
        from laboratory.utils_upload_reatives import create_shelfobject

        shelfobject = create_shelfobject(
            {
                "shelf": self.shelf,
                "object": self.catalog_object(row["name"]),
                "quantity": 1,
                "measurement_unit": Catalog.objects.get(key="units", description="Unidades"),
                "in_where_laboratory": self.laboratory,
                "created_by": self.user,
            },
            self.organization.pk,
            self.request,
        )
        return Characteristics.objects.create(
            shelfobject=shelfobject, organization=self.organization, created_by=self.user
        )

    def apply_fields(self, characteristics, row):
        for source, target in TEXT_FIELDS.items():
            value = (row.get(source) or "").strip()
            if value:
                setattr(characteristics, target, value[: characteristics._meta.get_field(target).max_length])
        magnitude = catalog_value("equipment_magnitude", row.get("magnitude"))
        if magnitude is not None:
            characteristics.magnitude = magnitude
        if row.get("custodian"):
            characteristics.custodian_id = row["custodian"]
        notes = (row.get("notes") or "").strip()
        if notes and notes not in (characteristics.notes or ""):
            characteristics.notes = "\n".join(part for part in (characteristics.notes, notes) if part)
        if row.get("authorized_users"):
            restriction = row["authorized_users"]
            if restriction not in characteristics.access_restrictions:
                characteristics.access_restrictions = restriction
        if row.get("decommissioned") and characteristics.equipment_status != Characteristics.DECOMMISSIONED:
            characteristics.equipment_status = Characteristics.DECOMMISSIONED
            characteristics.decommission_reason = characteristics.decommission_reason or _(
                "Marked as withdrawn in the imported spreadsheet."
            )
            shelfobject = characteristics.shelfobject
            shelfobject.marked_as_discard = True
            shelfobject.save(update_fields=["marked_as_discard"])
        characteristics.save()

    # -- programa PT-05 -----------------------------------------------------------------
    def plan(self, characteristics, kind, **defaults):
        plan, created = EquipmentActivityPlan.objects.get_or_create(
            shelfobject=characteristics.shelfobject,
            activity_kind=kind,
            defaults={"organization": self.organization, "created_by": self.user,
                      "responsible_id": characteristics.custodian_id, **defaults},
        )
        if created:
            self.summary["plans"] += 1
        return plan

    def apply_calibration(self, characteristics, row):
        date = row.get("calibration_date")
        if not date:
            return
        date = datetime.date.fromisoformat(date)
        next_date = row.get("next_calibration_date")
        next_date = datetime.date.fromisoformat(next_date) if next_date else None
        interval = months_between(date, next_date) if next_date and next_date > date else 12
        self.plan(characteristics, EquipmentActivityPlan.CALIBRATION, interval_value=interval or 12)
        _calibration, created = ShelfObjectCalibrate.objects.get_or_create(
            shelfobject=characteristics.shelfobject,
            calibration_date=date,
            defaults={
                "organization": self.organization,
                "created_by": self.user,
                "calibrate_name": _("Imported from the equipment program"),
                "next_calibration_date": next_date,
                "conformity": row.get("calibration_conformity", ""),
                "results": row.get("calibration_result", ""),
            },
        )
        if created:
            self.summary["calibrations"] += 1

    def apply_maintenance(self, characteristics, row):
        blocks = row.get("maintenance") or []
        if not blocks:
            return
        executed_date = row.get("maintenance_date")
        executed_date = datetime.date.fromisoformat(executed_date) if executed_date else None
        year = next((block["programmed_year"] for block in blocks if block.get("programmed_year")), None)
        activities = sorted({name for block in blocks for name in block.get("activities", [])})
        plan = self.plan(
            characteristics,
            EquipmentActivityPlan.PREVENTIVE_MAINTENANCE,
            interval_value=max(1, 12 // len(blocks)),
            start_date=datetime.date(year, 12, 31) if year else None,
            notes=_("Activities: %s") % ", ".join(activities) if activities else "",
        )
        executed = next((block for block in blocks if block.get("executed")), None)
        if executed_date is None or executed is None:
            return
        maintenance, created = ShelfObjectMaintenance.objects.get_or_create(
            shelfobject=characteristics.shelfobject,
            maintenance_date=executed_date,
            maintenance_type=executed["type"],
            defaults={
                "organization": self.organization,
                "created_by": self.user,
                "plan": plan,
                "affects_calibration": executed.get("affects_calibration", False),
                "damage_details": executed.get("damage_details", ""),
                "maintenance_observation": _("Imported from the equipment program"),
                "validator": getattr(self.user, "profile", None),
            },
        )
        if created:
            maintenance.activities.set(
                Catalog.objects.filter(key="maintenance_activity", description__in=executed.get("activities", []))
            )
            self.summary["maintenances"] += 1

    # -- fila -------------------------------------------------------------------------
    @transaction.atomic
    def import_row(self, row):
        characteristics = self.find(row.get("internal_code"))
        if characteristics is None:
            characteristics = self.create_unit(row)
            self.summary["created"] += 1
        else:
            self.summary["updated"] += 1
        self.apply_fields(characteristics, row)
        self.apply_calibration(characteristics, row)
        self.apply_maintenance(characteristics, row)
        return characteristics

    def import_rows(self, rows):
        for row in rows:
            if row.get("include", True):
                self.import_row(row)
        return self.summary
