from collections import defaultdict

from django.core.management.base import BaseCommand

from laboratory.models import Object, ShelfObject
from laboratory.utils_base_unit import cached_units, get_conversion_units, get_unit_info
from sga.models import SubstanceCharacteristics


def converted_quantity(unit, amount):
    """Lo mismo que guarda la señal ``shelf_object_base_quantity``."""
    if amount is None:
        return None
    value = get_conversion_units(unit, amount)
    return amount if value is None else value


def tons(base_description, value, density):
    """Toneladas con la misma fórmula del gráfico ``substancetonschart``."""
    if base_description == "Kilogramos":
        return value / 1000.0
    if base_description == "Libra":
        return value * 0.453592 / 1000.0
    if base_description == "Litros":
        return value * density / 1000.0
    if base_description == "Metro cúbico":
        return value * density
    return 0.0


class Command(BaseCommand):
    help = (
        "Mide, sin escribir nada, cuánto cambian quantity_base_unit y los totales que "
        "dependen de él (toneladas por organización y precursores por laboratorio) al "
        "expresarlo en la unidad base. Correr antes de la migración "
        "laboratory.0224_recalculate_quantity_base_unit; después ya no hay diferencias."
    )

    def add_arguments(self, parser):
        parser.add_argument("--organization", type=int, help="Acotar a una organización (pk)")

    def densities(self):
        """Densidad (kg/L) por objeto: la ficha SGA de menor pk; 0 o sin ficha -> 1."""
        result = {}
        rows = SubstanceCharacteristics.objects.filter(object_related__isnull=False).order_by(
            "object_related_id", "pk"
        ).values_list("object_related_id", "density")
        for object_id, density in rows:
            result.setdefault(object_id, density or 1.0)
        return result

    def handle(self, *args, **options):
        queryset = ShelfObject.objects.values_list(
            "pk",
            "object_id",
            "object__name",
            "object__type",
            "object__organization_id",
            "object__organization__name",
            "in_where_laboratory_id",
            "in_where_laboratory__name",
            "measurement_unit_id",
            "measurement_unit__description",
            "quantity",
            "quantity_base_unit",
            "is_box",
            "quantity_units",
            "object__substancharacteristics_object__is_precursor",
        ).order_by("pk")
        if options["organization"]:
            queryset = queryset.filter(object__organization_id=options["organization"])

        densities = self.densities()
        changed = defaultdict(int)
        tons_before = defaultdict(float)
        tons_after = defaultdict(float)
        org_names = {}
        precursors = defaultdict(lambda: [0.0, 0.0])
        seen = set()

        with cached_units():
            for (
                pk, object_id, object_name, object_type, org_id, org_name, lab_id, lab_name,
                unit_id, unit_name, quantity, stored, is_box, quantity_units, is_precursor,
            ) in queryset.iterator():
                if pk in seen:  # el JOIN con fichas SGA múltiples repite filas
                    continue
                seen.add(pk)
                info = get_unit_info(unit_id)
                after = converted_quantity(unit_id, quantity)
                org_names[org_id] = org_name
                if after is not None and abs((stored or 0) - after) > 1e-9:
                    changed[(org_id, unit_name)] += 1

                if object_type == Object.REACTIVE and info is not None:
                    density = densities.get(object_id, 1.0)
                    tons_before[org_id] += tons(info.base_description, stored or 0, density)
                    tons_after[org_id] += tons(info.base_description, after or 0, density)

                if is_precursor and quantity is not None:
                    total = quantity
                    if is_box and quantity_units:
                        total = sum(b.get("units", 0) for b in quantity_units) * quantity
                    base = info.base_description if info else unit_name
                    key = (lab_name or lab_id, object_name, base)
                    # Antes se sumaba la cantidad cruda; ahora convertida a la base.
                    precursors[key][0] += total
                    precursors[key][1] += converted_quantity(unit_id, total)

        self.stdout.write("Existencias cuyo quantity_base_unit cambia")
        if not changed:
            self.stdout.write("  ninguna")
        for (org_id, unit_name), count in sorted(changed.items(), key=lambda i: (str(org_names.get(i[0][0])), str(i[0][1]))):
            self.stdout.write(f"  {org_names.get(org_id)} · {unit_name}: {count}")

        self.stdout.write("\nToneladas por organización (gráfico substancetonschart)")
        for org_id in sorted(tons_after, key=lambda pk: str(org_names.get(pk))):
            before, after = tons_before[org_id], tons_after[org_id]
            if abs(before - after) > 1e-9:
                self.stdout.write(f"  {org_names.get(org_id)}: {before:.4f} t -> {after:.4f} t")

        self.stdout.write("\nPrecursores por laboratorio, objeto y unidad base")
        for (lab, object_name, base), (before, after) in sorted(precursors.items(), key=lambda i: tuple(map(str, i[0]))):
            if abs(before - after) > 1e-9:
                self.stdout.write(f"  {lab} · {object_name} · {base}: {before:g} -> {after:g}")
