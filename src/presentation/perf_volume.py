# encoding: utf-8
"""Datos sintéticos a escala para medir cómo crecen los reportes.

Una **unidad de escala** es un laboratorio completo de la organización 1 de
`laboratory_data.json`: salas, muebles, estantes (uno de desecho por mueble), objetos
con características SGA, `ShelfObject` con límites y donaciones, bitácora de cambios,
límites máximos (regencia), un edificio con su zona de riesgo y puntos de consumo
ambiental con un año de registros. `seed(units, start)` añade unidades nuevas sin tocar
las anteriores, así las escalas se acumulan (1 → 10 → 100).

Se usa `bulk_create` por volumen. Lo que eso se salta (señales de `ShelfObject`:
código de lote, cantidad en unidad base, correo de límites) no lo leen los reportes;
`ConsumptionRecord` sí calcula costos y `is_waste` en `save()`, por eso se guarda uno
a uno.
"""

import datetime
import random
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.utils import timezone

# Tamaño de una unidad. 2 salas × 3 muebles × 4 estantes × 10 = 240 ShelfObject.
ROOMS = 2
FURNITURE_PER_ROOM = 3
SHELVES_PER_FURNITURE = 4
SHELFOBJECTS_PER_SHELF = 10
OBJECTS = 40
LOGS_PER_SHELFOBJECT = 2
MONTHS = 12

PHYSICAL = ("liquid", "solid powder", "solid granular or crystalline", "Gaseous")

ORG_PK = 1
USER_PK = 1


def guard_database():
    """Nunca sembrar fuera de una base de prueba."""
    name = connection.settings_dict["NAME"]
    if not str(name).startswith("test_"):
        raise RuntimeError("seed_volume solo corre sobre una base test_*, no sobre %r" % name)


class Catalogs:
    """Pks reales de los catálogos que hacen falta; se resuelven una vez."""

    def __init__(self):
        from laboratory.models import BaseUnitValues, Catalog

        with_base = set(BaseUnitValues.objects.values_list("measurement_unit_id", flat=True))
        toneladas = set(Catalog.objects.filter(key="units", description__icontains="tonelada").values_list("pk", flat=True))
        # Solo unidades con BaseUnitValues: stock y riesgo revientan sin ella.
        self.units = sorted(with_base - toneladas)
        self.furniture_type = self._first("furniture_type")
        self.container_type = self._first("container_type")
        self.status = self._first("shelfobject_status")
        if not self.units:
            raise RuntimeError("no hay unidades con BaseUnitValues en la base")

    def _first(self, key):
        from laboratory.models import Catalog

        return Catalog.objects.filter(key=key).values_list("pk", flat=True).first()


def _set_dates(model, pks, field, days):
    """Reparte en el último año un campo auto_now_add que bulk_create dejó en now()."""
    now = timezone.now()
    for pk in pks:
        model.objects.filter(pk=pk).update(**{field: now - datetime.timedelta(days=random.randint(0, days))})


@transaction.atomic
def seed(units, start=0, seed_value=1234):
    """Añade `units` unidades de escala, numeradas desde `start`."""
    from laboratory import dataconfig
    from laboratory.models import (
        Furniture, Laboratory, LaboratoryRoom, Object, ObjectLogChange, ObjectMaximumLimit,
        OrganizationStructure, OrganizationStructureRelations, Shelf, ShelfObject, ShelfObjectLimits,
        UserOrganization,
    )
    from risk_management.models import Buildings, RiskZone, ZoneType
    from sga.models import DangerIndication, SubstanceCharacteristics

    guard_database()
    rnd = random.Random(seed_value + start)
    cat = Catalogs()
    org = OrganizationStructure.objects.get(pk=ORG_PK)
    user = User.objects.get(pk=USER_PK)
    # Los reportes ambientales filtran por los edificios del autor: superusuario los ve todos.
    if not user.is_superuser:
        user.is_superuser = True
        user.save(update_fields=["is_superuser"])
    # report_objects y el de reactivos por organización exigen membresía.
    UserOrganization.objects.get_or_create(organization=org, user=user, defaults={"status": True, "type_in_organization": 1})
    lab_ct = ContentType.objects.get_for_model(Laboratory)
    h_codes = list(DangerIndication.objects.values_list("pk", flat=True)[:30])
    zone_type = ZoneType.objects.first() or ZoneType.objects.create(name="Volumen")

    for unit in range(start, start + units):
        lab = Laboratory.objects.create(name="Vol lab %d" % unit, organization=org, created_by=user)
        OrganizationStructureRelations.objects.create(organization=org, content_type=lab_ct, object_id=lab.pk)

        objects = Object.objects.bulk_create([
            Object(name="Vol obj %d-%d" % (unit, i), type=str(i % 3 if i % 5 else 0), organization=org, created_by=user)
            for i in range(OBJECTS)
        ])
        reactives = [o for o in objects if o.type == "0"]
        chars = SubstanceCharacteristics.objects.bulk_create([
            SubstanceCharacteristics(
                object_related=o, cas_id_number="%d-%02d-%d" % (1000 + o.pk, o.pk % 100, o.pk % 10),
                molecular_formula="C%dH%d" % (o.pk % 9 + 1, o.pk % 7 + 1), is_precursor=(o.pk % 4 == 0),
            )
            for o in reactives
        ])
        if h_codes:
            through = SubstanceCharacteristics.h_code.through
            through.objects.bulk_create([
                through(substancecharacteristics_id=c.pk, dangerindication_id=code)
                for c in chars for code in rnd.sample(h_codes, min(3, len(h_codes)))
            ])

        rooms = LaboratoryRoom.objects.bulk_create([
            LaboratoryRoom(laboratory=lab, name="Sala %d" % r, created_by=user) for r in range(ROOMS)])
        furniture = Furniture.objects.bulk_create([
            Furniture(labroom=room, name="Mueble %d" % f, type_id=cat.furniture_type, dataconfig="[]", created_by=user)
            for room in rooms for f in range(FURNITURE_PER_ROOM)])
        shelves = []
        for item in furniture:
            group = Shelf.objects.bulk_create([
                Shelf(furniture=item, name="Estante %d" % s, type_id=cat.container_type,
                      discard=(s == SHELVES_PER_FURNITURE - 1), created_by=user)
                for s in range(SHELVES_PER_FURNITURE)])
            # Una columna por estante: el mapa de riesgo lee el acomodo desde aquí.
            item.dataconfig = dataconfig.dump([[[shelf.pk] for shelf in group]])
            shelves += group
        Furniture.objects.bulk_update(furniture, ["dataconfig"])

        limits = ShelfObjectLimits.objects.bulk_create([
            ShelfObjectLimits(minimum_limit=5, maximum_limit=50)
            for _ in range(len(shelves) * SHELFOBJECTS_PER_SHELF)])
        shelfobjects = []
        for index, (shelf, slot) in enumerate((s, n) for s in shelves for n in range(SHELFOBJECTS_PER_SHELF)):
            obj = rnd.choice(objects)
            # Uno de cada siete queda justo en el mínimo: report_limit_objects solo lista esos.
            quantity = 5 if index % 7 == 0 else round(rnd.uniform(1, 100), 2)
            shelfobjects.append(ShelfObject(
                shelf=shelf, object=obj, quantity=quantity, measurement_unit_id=rnd.choice(cat.units),
                status_id=cat.status, in_where_laboratory=lab, limits=limits[index], created_by=user,
                was_donated=(index % 10 == 0),
                physical_status=None if obj.type != "0" else PHYSICAL[index % len(PHYSICAL)]))
        shelfobjects = ShelfObject.objects.bulk_create(shelfobjects)
        _set_dates(ShelfObject, [so.pk for so in shelfobjects[::5]], "creation_date", 365)

        logs = ObjectLogChange.objects.bulk_create([
            ObjectLogChange(
                object=so.object, laboratory=lab, user=user, measurement_unit_id=so.measurement_unit_id,
                old_value=so.quantity, new_value=so.quantity + n, diff_value=n, precursor=(so.object.pk % 4 == 0),
                type_action=n % 3)
            for so in shelfobjects for n in range(LOGS_PER_SHELFOBJECT)])
        _set_dates(ObjectLogChange, [log.pk for log in logs[::4]], "update_time", 365)

        limits = ObjectMaximumLimit.objects.bulk_create([
            ObjectMaximumLimit(laboratory=lab, object=o, quantity=round(rnd.uniform(10, 1000), 1),
                               measurement_unit_id=rnd.choice(cat.units))
            for o in reactives])
        # El reporte de regencia mira el año anterior: con `auto_now_add` los
        # límites quedaban en el año en curso y el reporte salía vacío.
        ObjectMaximumLimit.objects.filter(pk__in=[limit.pk for limit in limits]).update(
            created_at=datetime.date(timezone.now().year - 1, 6, 30))

        building = Buildings.objects.create(name="Edificio vol %d" % unit, phone="2222-2222", organization=org, created_by=user)
        building.laboratories.add(lab)
        zone = RiskZone.objects.create(name="Zona vol %d" % unit, num_workers=10, zone_type=zone_type, organization=org,
                                       created_by=user)
        zone.laboratories.add(lab)
        zone.buildings.add(building)

        _seed_ambiental(org, user, building, unit, rnd)


def _seed_ambiental(org, user, building, unit, rnd):
    from ambiental.models import ConsumptionRecord, MeasurementPoint
    from laboratory.models import Catalog

    point_type = Catalog.objects.filter(key="ambiental_point_type").first()
    measure_units = list(Catalog.objects.filter(key="ambiental_measure_unit"))
    if point_type is None or not measure_units:
        return
    year = timezone.now().year - 1
    for resource in Catalog.objects.filter(key="ambiental_resource_type"):
        point = MeasurementPoint.objects.create(
            organization=org, created_by=user, code="V%d-%d" % (unit, resource.pk), name="Medidor %s" % resource.description,
            point_type=point_type, resource_type=resource, building=building)
        for month in range(1, MONTHS + 1):
            start = datetime.date(year, month, 1)
            end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
            # save() uno a uno: calcula costos y marca los residuos.
            ConsumptionRecord.objects.create(
                organization=org, created_by=user, point=point, period_start=start, period_end=end,
                quantity=Decimal("%.2f" % rnd.uniform(1, 500)), unit=rnd.choice(measure_units))


def data_size():
    """Volumen que ven los reportes: ShelfObject y bitácora de la organización."""
    from ambiental.models import ConsumptionRecord
    from laboratory.models import ObjectLogChange, ShelfObject

    return {
        "shelfobjects": ShelfObject.objects.count(),
        "logs": ObjectLogChange.objects.count(),
        "consumption": ConsumptionRecord.objects.count(),
    }


# -- payloads -----------------------------------------------------------------

def payload(report_name, file_type, labs):
    """`data` tal como lo dejaría el formulario (cleaned_data + org_pk)."""
    from laboratory.models import Furniture, LaboratoryRoom

    year = timezone.now().year - 1
    period = "01/01/%d - 31/12/%d" % (year, year)
    data = {"org_pk": ORG_PK, "organization": ORG_PK, "name": "vol-%s" % report_name, "title": "Volumen",
            "report_name": report_name, "format": file_type, "laboratory": labs}
    extra = {
        "report_laboratory_room": None,
        "report_furniture": None,
        "report_objects": {"object_type": ""},
        "report_objectschanges": {"period": period, "precursor": False, "resume": False},
        "report_organization_reactive_list": {"users": [USER_PK]},
        "report_waste_objects": {"period": ""},
        "risk_zone_report": {"risk_zone": [], "building": []},
        "regency_report": {"period": period, "years": year},
        "compatibility_report": {"risk_zone": [], "building": []},
        "report_consumption_detail": {"building": [], "resource_type": [], "period": period},
        "report_consumption_summary": {"building": [], "resource_type": [], "period": period},
        "report_consumption_cost": {"building": [], "resource_type": [], "period": period},
        "report_waste_manifest": {"building": [], "resource_type": [], "period": period},
        "report_environmental_indicators": {"building": [], "resource_type": [], "normalizer": [], "period": period},
        "report_consumption_comparison": {
            "building": [], "resource_type": [], "period": period,
            "comparison_period": "01/01/%d - 31/12/%d" % (year - 1, year - 1)},
    }
    if report_name in ("report_laboratory_room", "report_furniture"):
        rooms = list(LaboratoryRoom.objects.filter(laboratory__in=labs).values_list("pk", flat=True))
        data.update(lab_room=rooms, object_type="", is_precursor=False,
                    furniture=list(Furniture.objects.filter(labroom__in=rooms).values_list("pk", flat=True)))
    elif extra.get(report_name):
        data.update(extra[report_name])
    return data
