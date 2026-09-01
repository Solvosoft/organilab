"""Equivalencia del hazard_map antes/despues del refactor.

Reimplementa la version ANTERIOR tal cual estaba y compara su salida con la
nueva sobre los datos del fixture.
"""
import json

from laboratory.models import (
    Catalog,
    Furniture,
    Laboratory,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)
from sga.models import DangerIndication, SubstanceCharacteristics
from risk_management.hazard_map_utils import (
    HAZARD_COLORS,
    build_lab_hazard_map,
    compute_lab_risk,
    compute_tonnage_aggregates,
    collect_room_shelf_hcodes,
    compute_shelf_danger,
    compute_lab_tonnage,
    _collect_alerts,
    _shelf_to_dict,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest


def _old_parse_cell(cell):
    if not cell:
        return []
    if isinstance(cell, int):
        return [cell]
    if isinstance(cell, str):
        out = []
        for p in cell.split(","):
            p = p.strip()
            if p:
                try:
                    out.append(int(p))
                except (ValueError, TypeError):
                    pass
        return out
    if isinstance(cell, list):
        out = []
        for item in cell:
            if isinstance(item, int):
                out.append(item)
            elif isinstance(item, str):
                try:
                    out.append(int(item.strip()))
                except (ValueError, TypeError):
                    pass
        return out
    return []


def _old_grid(furniture, shelf_colors):
    grid = []
    if not furniture.dataconfig:
        shelves = Shelf.objects.filter(furniture=furniture)
        if shelves.exists():
            grid.append([{"shelves": [_shelf_to_dict(s, shelf_colors) for s in shelves]}])
        return grid
    try:
        dataconfig = json.loads(furniture.dataconfig)
    except (json.JSONDecodeError, TypeError):
        return grid
    for row in dataconfig:
        grid_row = []
        for cell in row:
            cell_shelves = []
            for pk in _old_parse_cell(cell):
                try:
                    shelf = Shelf.objects.get(pk=pk)
                except Shelf.DoesNotExist:
                    continue
                cell_shelves.append(_shelf_to_dict(shelf, shelf_colors))
            grid_row.append({"shelves": cell_shelves})
        grid.append(grid_row)
    return grid


def _old_build(laboratory):
    rooms_data = []
    summary = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    alerts = []
    for room in LaboratoryRoom.objects.filter(laboratory=laboratory):
        all_shelves_data = collect_room_shelf_hcodes(room)
        shelf_colors = {}
        for shelf_pk, sdata in all_shelves_data.items():
            compat_code, worst_pair = compute_shelf_danger(
                shelf_pk, sdata["h_codes"], all_shelves_data
            )
            shelf_colors[shelf_pk] = {
                "compat_code": compat_code,
                "color": HAZARD_COLORS.get(compat_code, HAZARD_COLORS["-"]),
                "worst_pair": worst_pair,
                "substances": sdata["substances"],
                "name": sdata["name"],
            }
            if compat_code == "V":
                summary["green"] += 1
            elif compat_code == "A":
                summary["yellow"] += 1
            elif compat_code == "R":
                summary["red"] += 1
            else:
                summary["gray"] += 1
        _collect_alerts(all_shelves_data, alerts)
        furniture_list = [
            {"name": f.name, "pk": f.pk, "grid": _old_grid(f, shelf_colors)}
            for f in Furniture.objects.filter(labroom=room)
        ]
        rooms_data.append({"name": room.name, "furniture_list": furniture_list})
    return {
        "laboratory": laboratory.name,
        "laboratory_pk": laboratory.pk,
        "rooms": rooms_data,
        "summary": summary,
        "alerts": alerts,
        "tonnage": compute_lab_tonnage(laboratory),
    }


def _plain(value):
    """Los shelves llevan instancias; se comparan por su representacion."""
    return json.loads(json.dumps(value, default=str, sort_keys=True))


class HazardMapEquivalenceTest(BaseLaboratorySetUpTest):
    """El refactor no puede cambiar ni un byte de la salida del mapa.

    El fixture por si solo es demasiado pobre para demostrarlo: un unico
    estante con codigos H, ninguna alerta y cero masa. ``setUp`` monta el
    escenario que si ejercita las ramas que importan -- dos estantes
    incompatibles en la misma sala, un mueble con cuadricula irregular y
    reactivos con unidades convertibles a kilogramos.
    """

    def setUp(self):
        super().setUp()
        corrosive = DangerIndication.objects.get(code="H314")
        flammable = DangerIndication.objects.get(code="H225")
        oxidizer = DangerIndication.objects.get(code="H272")

        # Un reactivo por codigo, cada uno en un estante distinto de la MISMA
        # sala: compute_shelf_danger solo compara entre estantes hermanos.
        kilograms = Catalog.objects.get(key="units", description="Kilogramos")
        room_shelves = [
            (Shelf.objects.get(pk=1), corrosive),
            (Shelf.objects.get(pk=2), flammable),
            (Shelf.objects.get(pk=3), oxidizer),
        ]
        for index, (shelf, hcode) in enumerate(room_shelves):
            obj = Object.objects.create(
                code="EQ-%d" % index,
                name="Reactivo %d" % index,
                type=Object.REACTIVE,
                organization=self.org,
            )
            characteristics = SubstanceCharacteristics.objects.create(object_related=obj)
            characteristics.h_code.add(hcode)
            ShelfObject.objects.create(
                object=obj,
                shelf=shelf,
                quantity=12.5,
                measurement_unit=kilograms,
                in_where_laboratory=self.lab,
                created_by=self.user,
            )

        # Cuadricula irregular: una fila de dos celdas y otra de cuatro.
        furniture = Shelf.objects.get(pk=1).furniture
        furniture.dataconfig = "[[[1],[2]],[[3],[],[],[]]]"
        furniture.save()

    def test_build_lab_hazard_map_is_unchanged(self):
        for lab in Laboratory.objects.all():
            with self.subTest(lab=lab.pk):
                self.assertEqual(
                    _plain(_old_build(lab)), _plain(build_lab_hazard_map(lab))
                )

    def test_the_scenario_actually_exercises_the_risk_branches(self):
        """Sin esto la equivalencia podria pasar comparando dos ceros."""
        risk = compute_lab_risk(self.lab)
        self.assertGreaterEqual(len(risk["shelf_colors"]), 3)
        self.assertTrue(risk["alerts"], "el escenario no genero ninguna alerta")
        self.assertTrue(
            any(value for key, value in risk["summary"].items() if key != "gray"),
            "ningun estante quedo clasificado",
        )
        tonnage = compute_tonnage_aggregates(self.lab)
        self.assertGreater(tonnage["laboratory"]["kilograms"], 0)
        self.assertTrue(tonnage["rooms"], "no hubo desglose por sala")
        self.assertTrue(tonnage["furniture"], "no hubo desglose por mueble")
