"""Bases de normalización: los denominadores de los indicadores ambientales.

Funciones sin estado de petición, para poder llamarlas desde la API, los reportes y
las tareas programadas, y probarlas sin cliente HTTP.
"""
from decimal import Decimal

from django.db.models import Sum

from ambiental.ambiental_defaults import (
    KEY_NORMALIZER,
    NORMALIZER_AREA,
    NORMALIZER_PERSON,
)
from ambiental.models import NormalizationBase
from laboratory.models import Catalog
from risk_management.models import Buildings, Workday


def building_area(building):
    """Los m² del edificio. ``Buildings.area`` no guarda unidad: se asume m²."""
    if building.area and building.area > 0:
        return Decimal(str(building.area)).quantize(Decimal("0.01"))
    return None


def building_people(building):
    """Personas por jornada en las zonas de riesgo de los laboratorios del edificio.

    Una zona de riesgo puede cubrir varios laboratorios del mismo edificio: se suma
    cada jornada **una sola vez**, o las personas se contarían tantas veces como
    laboratorios tenga la zona.
    """
    workday_ids = (
        Workday.objects.filter(risk_zone__laboratories__buildings=building)
        .values_list("pk", flat=True)
        .distinct()
    )
    total = Workday.objects.filter(pk__in=list(workday_ids)).aggregate(
        total=Sum("num_workers")
    )["total"]
    if total:
        return Decimal(total)
    return None


PRELOADERS = {
    NORMALIZER_AREA: building_area,
    NORMALIZER_PERSON: building_people,
}


def preload_bases(organization, year, user=None):
    """Crea o actualiza las bases deducidas del año para cada edificio de la organización.

    Devuelve las bases tocadas y lo que se saltó, para que quien llama deje bitácora.
    Nunca pisa una base escrita a mano.
    """
    result = {"created": [], "updated": [], "skipped": 0}
    normalizers = {
        item.description: item
        for item in Catalog.objects.filter(key=KEY_NORMALIZER, description__in=PRELOADERS)
    }
    for building in Buildings.objects.filter(organization=organization):
        for description, preloader in PRELOADERS.items():
            normalizer = normalizers.get(description)
            value = preloader(building)
            if normalizer is None or value is None:
                result["skipped"] += 1
                continue
            base = NormalizationBase.objects.filter(
                organization=organization, normalizer=normalizer, building=building, year=year
            ).first()
            if base is None:
                base = NormalizationBase.objects.create(
                    organization=organization,
                    normalizer=normalizer,
                    building=building,
                    year=year,
                    value=value,
                    is_manual=False,
                    created_by=user,
                )
                result["created"].append(base)
            elif base.is_manual or base.value == value:
                result["skipped"] += 1
            else:
                base.value = value
                base.save(update_fields=["value", "last_update"])
                result["updated"].append(base)
    return result


def get_base(organization, building, normalizer, year):
    """La base vigente para el año: la del propio año o, si falta, la del último anterior.

    Devuelve la fila (su ``year`` dice si es heredada) o ``None``.
    """
    return (
        NormalizationBase.objects.filter(
            organization=organization,
            building=building,
            normalizer=normalizer,
            year__lte=year,
        )
        .order_by("-year")
        .first()
    )
