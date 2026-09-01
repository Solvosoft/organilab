"""El mapa completo del laboratorio en una sola respuesta.

Salas, muebles con su cuadrícula real, estantes con nombre, tipo, posición,
capacidad, ocupación y descarte, más conteos agregados y —cuando se pide— el
color de riesgo.  Se construye en un puñado de consultas frente al N+1 por
celda que hacía el mapa de peligros.

Las cuadrículas viajan como ``{"cells": [[...], [...]]}`` **sin** ``rows`` ni
``cols``: las filas son irregulares porque la forma la define el usuario según
cómo sea su laboratorio, y un ancho único mentiría sobre ella.
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum
from django.urls import reverse

from laboratory import dataconfig
from laboratory.models import Furniture, LaboratoryRoom, Shelf, ShelfObject
from presentation.models import QRModel
from presentation.utils import build_qr_instance

#: Capacidades que la interfaz consulta para decidir qué pintar.  Se envían
#: para *mostrar*; cada endpoint vuelve a exigir la suya para *autorizar*.
TREE_PERMISSIONS = [
    "laboratory.add_laboratoryroom",
    "laboratory.change_laboratoryroom",
    "laboratory.delete_laboratoryroom",
    "laboratory.view_laboratoryroom",
    "laboratory.add_furniture",
    "laboratory.change_furniture",
    "laboratory.delete_furniture",
    "laboratory.view_furniture",
    "laboratory.add_shelf",
    "laboratory.change_shelf",
    "laboratory.delete_shelf",
    "laboratory.view_shelf",
    "laboratory.add_shelfobject",
    "laboratory.change_shelfobject",
    "laboratory.delete_shelfobject",
    "laboratory.view_shelfobject",
    "laboratory.view_shelfobjectobservation",
    "laboratory.can_manage_disposal",
    "laboratory.do_report",
    "laboratory.add_tranferobject",
    "sga.view_recipientsize",
    "sga.add_recipientsize",
    "reservations_management.add_reservedproducts",
]


def get_permissions(user):
    """``{"add_furniture": bool, ...}`` — sin el prefijo de la app."""
    return {
        codename.split(".", 1)[1]: user.has_perm(codename)
        for codename in TREE_PERMISSIONS
    }


class TreeBuilder:
    """Arma el árbol de un laboratorio.

    ``risk=True`` añade el color de cada estante y los agregados por zona; sin
    el flag no se calcula nada, porque el overlay es una decisión explícita del
    usuario y la navegación normal no debe pagarla.
    """

    def __init__(self, organization, laboratory, user, risk=False, request=None):
        self.organization = organization
        self.laboratory = laboratory
        self.user = user
        self.risk = risk
        self.request = request

    # -- consultas ---------------------------------------------------------

    def get_rooms(self):
        return list(
            LaboratoryRoom.objects.filter(laboratory=self.laboratory).order_by("pk")
        )

    def get_furniture(self, rooms):
        return list(
            Furniture.objects.filter(labroom__in=rooms).select_related("type", "labroom")
        )

    def get_shelves(self, furniture):
        """Todos los estantes del laboratorio, en una consulta.

        Se piden por mueble y no por los pks de los ``dataconfig``: un estante
        que existe pero todavía no ocupa una celda tiene que aparecer, porque
        si no la interfaz no ofrecería forma de colocarlo.
        """
        shelves = Shelf.objects.filter(furniture__in=furniture).select_related(
            "type", "measurement_unit", "furniture"
        )
        return {shelf.pk: shelf for shelf in shelves}

    def get_shelfobject_counts(self, furniture):
        rows = (
            ShelfObject.objects.filter(shelf__furniture__in=furniture)
            .values("shelf")
            .annotate(total=Count("pk"))
        )
        return {row["shelf"]: row["total"] for row in rows}

    def get_occupancy(self, furniture):
        """Cantidad acumulada por estante, sin contar lo que hay en contenedores."""
        rows = (
            ShelfObject.objects.filter(
                shelf__furniture__in=furniture, containershelfobject=None
            )
            .values("shelf", "measurement_unit")
            .annotate(amount=Sum("quantity"))
        )
        totals = {}
        for row in rows:
            totals.setdefault(row["shelf"], {})[row["measurement_unit"]] = (
                row["amount"] or 0
            )
        return totals

    def get_qr_map(self, rooms, furniture, shelves):
        """Los QR de cada nodo, en una consulta por tipo.

        Los que falten se crean aquí, igual que hacía ``get_qr_svg_img`` al
        pintar la plantilla antigua: si no, una sala o un estante recién
        creados se quedarían sin QR y el usuario perdería una función que hoy
        tiene sin pedir nada.
        """
        qr_map = {}
        for model, objects, deep_link in (
            (LaboratoryRoom, rooms, lambda obj: self.deep_link(labroom=obj.pk)),
            (
                Furniture,
                furniture,
                lambda obj: self.deep_link(
                    labroom=obj.labroom_id, furniture=obj.pk
                ),
            ),
            (
                Shelf,
                list(shelves.values()),
                lambda obj: self.deep_link(
                    labroom=obj.furniture.labroom_id,
                    furniture=obj.furniture_id,
                    shelf=obj.pk,
                ),
            ),
        ):
            if not objects:
                continue
            content_type = ContentType.objects.get_for_model(model)
            rows = QRModel.objects.filter(
                content_type=content_type,
                organization=self.organization,
                object_id__in=[obj.pk for obj in objects],
            ).values("object_id", "b64_image")
            found = {row["object_id"]: row["b64_image"] for row in rows}
            for obj in objects:
                if obj.pk not in found:
                    qr = build_qr_instance(
                        self.absolute(deep_link(obj)), obj, self.organization.pk
                    )
                    found[obj.pk] = qr.b64_image
            qr_map[model.__name__] = found
        return qr_map

    def absolute(self, path):
        """El QR se imprime y se escanea fuera: necesita la URL completa."""
        if self.request is None:
            return path
        return self.request.build_absolute_uri(path)

    # -- enlaces -----------------------------------------------------------

    def deep_link(self, labroom=None, furniture=None, shelf=None):
        """El contrato de siempre: ``?labroom=&furniture=&shelf=``.

        Es el mismo query string que llevan los QR impresos y los enlaces del
        mapa de peligros, de modo que un enlace copiado desde aquí y uno
        pegado en la pared abran lo mismo.
        """
        base = reverse(
            "laboratory:labview",
            kwargs={"org_pk": self.organization.pk, "lab_pk": self.laboratory.pk},
        )
        parts = []
        if labroom is not None:
            parts.append("labroom=%d" % labroom)
        if furniture is not None:
            parts.append("furniture=%d" % furniture)
        if shelf is not None:
            parts.append("shelf=%d" % shelf)
        return base + ("?" + "&".join(parts) if parts else "")

    # -- construcción ------------------------------------------------------

    def build(self):
        rooms = self.get_rooms()
        furniture = self.get_furniture(rooms)

        grids = {item.pk: dataconfig.parse(item.dataconfig) for item in furniture}
        shelves = self.get_shelves(furniture)
        counts = self.get_shelfobject_counts(furniture)
        occupancy = self.get_occupancy(furniture)
        qr_map = self.get_qr_map(rooms, furniture, shelves)
        risk = self.build_risk() if self.risk else None

        by_room = {}
        for item in furniture:
            by_room.setdefault(item.labroom_id, []).append(item)

        return {
            "laboratory": {"id": self.laboratory.pk, "name": self.laboratory.name},
            "permissions": get_permissions(self.user),
            "risk_enabled": bool(self.risk),
            "rooms": [
                self.build_room(
                    room, by_room.get(room.pk, []), grids, shelves, counts,
                    occupancy, qr_map, risk,
                )
                for room in rooms
            ],
        }

    def build_shelves_of(self, furniture):
        """Los nodos de estante de UN mueble, con la forma exacta del árbol.

        El editor repinta con lo que responde el servidor, así que la respuesta
        de una operación de cuadrícula tiene que traer los mismos campos que el
        árbol: si trae menos, el repintado se cae y la pantalla se queda
        mostrando un estado que ya no es el de la base de datos.
        """
        items = [furniture]
        grid = dataconfig.parse(furniture.dataconfig)
        shelves = self.get_shelves(items)
        counts = self.get_shelfobject_counts(items)
        occupancy = self.get_occupancy(items)
        qr_map = self.get_qr_map([], items, shelves)
        risk = self.build_risk() if self.risk else None

        return {
            "grid": {"cells": grid},
            "shelves": {
                str(pk): self.build_shelf(
                    shelf, grid, counts, occupancy, qr_map, risk
                )
                for pk, shelf in shelves.items()
            },
        }

    def build_room(self, room, furniture, grids, shelves, counts, occupancy,
                   qr_map, risk):
        furniture_data = [
            self.build_furniture(
                item, grids[item.pk], shelves, counts, occupancy, qr_map, risk
            )
            for item in furniture
        ]
        shelf_total = sum(item["counts"]["shelves"] for item in furniture_data)
        object_total = sum(item["counts"]["shelfobjects"] for item in furniture_data)

        return {
            "id": room.pk,
            "name": room.name,
            "qr": qr_map.get("LaboratoryRoom", {}).get(room.pk),
            "deep_link": self.deep_link(labroom=room.pk),
            "counts": {
                "furniture": len(furniture_data),
                "shelves": shelf_total,
                "shelfobjects": object_total,
            },
            "risk": self.room_risk(room, risk),
            "furniture": furniture_data,
        }

    def build_furniture(self, item, grid, shelves, counts, occupancy, qr_map, risk):
        own_shelves = {
            pk: shelf for pk, shelf in shelves.items() if shelf.furniture_id == item.pk
        }
        placed = set(dataconfig.iter_shelf_pks(grid))
        # Un estante sin celda no puede desaparecer del mapa: se muestra en una
        # bandeja aparte para que el editor pueda colocarlo.
        unplaced = sorted(pk for pk in own_shelves if pk not in placed)

        return {
            "id": item.pk,
            "name": item.name,
            "type": item.type_id,
            "type_name": str(item.type) if item.type else "",
            "color": item.color,
            "labroom": item.labroom_id,
            "qr": qr_map.get("Furniture", {}).get(item.pk),
            "deep_link": self.deep_link(labroom=item.labroom_id, furniture=item.pk),
            # El reporte del mueble ya existe y se pide por query string; se
            # arma aquí para que el mapa lo ofrezca sin consultar nada más.
            "report_url": "%s?laboratory=%d&furniture=%d"
            % (
                reverse(
                    "report:reports_furniture_detail",
                    kwargs={"org_pk": self.organization.pk},
                ),
                self.laboratory.pk,
                item.pk,
            ),
            "grid": {"cells": grid},
            "unplaced": unplaced,
            "shelves": {
                str(pk): self.build_shelf(
                    shelf, grid, counts, occupancy, qr_map, risk
                )
                for pk, shelf in own_shelves.items()
            },
            "counts": {
                "shelves": len(own_shelves),
                "shelfobjects": sum(counts.get(pk, 0) for pk in own_shelves),
            },
            "risk": self.furniture_risk(item, own_shelves, risk),
        }

    def build_shelf(self, shelf, grid, counts, occupancy, qr_map, risk):
        row, col = dataconfig.get_position(grid, shelf.pk)
        return {
            "id": shelf.pk,
            "name": shelf.name,
            "type": shelf.type_id,
            "type_name": str(shelf.type) if shelf.type else "",
            "color": shelf.color,
            "description": shelf.description or "",
            "discard": shelf.discard,
            "position": [row, col],
            "quantity": shelf.quantity,
            "measurement_unit": shelf.get_measurement_unit_display(),
            "infinity_quantity": shelf.infinity_quantity,
            "occupancy_percent": self.occupancy_percent(shelf, occupancy),
            "counts": {"shelfobjects": counts.get(shelf.pk, 0)},
            "qr": qr_map.get("Shelf", {}).get(shelf.pk),
            "deep_link": self.deep_link(
                labroom=shelf.furniture.labroom_id,
                furniture=shelf.furniture_id,
                shelf=shelf.pk,
            ),
            "risk": self.shelf_risk(shelf.pk, risk),
        }

    def occupancy_percent(self, shelf, occupancy):
        # Sin unidad o con capacidad infinita el porcentaje no significa nada.
        if shelf.infinity_quantity or not shelf.measurement_unit_id:
            return None
        if not shelf.quantity:
            return None
        amount = occupancy.get(shelf.pk, {}).get(shelf.measurement_unit_id, 0)
        return round((amount / shelf.quantity) * 100, 2)

    # -- riesgo ------------------------------------------------------------

    def build_risk(self):
        # El import es local porque risk_management depende de laboratory: a
        # nivel de módulo el ciclo rompe el arranque.
        from risk_management.hazard_map_utils import (
            compute_lab_risk,
            compute_tonnage_aggregates,
        )

        risk = compute_lab_risk(self.laboratory)
        risk["tonnage"] = compute_tonnage_aggregates(self.laboratory)
        return risk

    def shelf_risk(self, shelf_pk, risk):
        if risk is None:
            return None
        info = risk["shelf_colors"].get(shelf_pk)
        if info is None:
            return {"compat_code": "-", "color": None, "hcodes": [], "worst_pair": ""}
        return {
            "compat_code": info["compat_code"],
            "color": info["color"],
            "hcodes": risk["shelf_hcodes"].get(shelf_pk, []),
            "worst_pair": info["worst_pair"],
        }

    def room_risk(self, room, risk):
        if risk is None:
            return None
        room_risk = risk["rooms"].get(room.pk, {})
        return {
            "summary": room_risk.get("summary"),
            "alerts": room_risk.get("alerts", 0),
            "tonnage": risk["tonnage"]["rooms"].get(room.pk),
        }

    def furniture_risk(self, item, own_shelves, risk):
        if risk is None:
            return None
        worst = "-"
        order = {"-": 0, "V": 1, "A": 2, "R": 3}
        for pk in own_shelves:
            info = risk["shelf_colors"].get(pk)
            if info and order[info["compat_code"]] > order[worst]:
                worst = info["compat_code"]
        return {
            "compat_code": worst,
            "tonnage": risk["tonnage"]["furniture"].get(item.pk),
        }
