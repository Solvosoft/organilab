# encoding: utf-8
"""Inventario de funciones: ninguna de la vista vieja puede perderse.

Traducción de la tabla «Funciones que NO se pueden perder» de
``roadmap/14_ETAPA_LABVIEW.md`` a aserciones.  Cada fila del roadmap es una
entrada de :data:`INVENTORY`, y el mensaje de fallo es el texto de esa fila:
si mañana se pierde el QR del estante, la suite dice «Estante / QR propio» en
vez de un ``KeyError`` sin contexto.

Lo que cambia respecto a la vista vieja es de dónde sale el dato, no lo que el
usuario puede hacer.  Por eso todas las aserciones son sobre el payload —el
árbol, el diccionario de acciones o las rutas que la vista entrega al
JavaScript— y ninguna sobre HTML.
"""

import base64
from collections import namedtuple

from django.urls import reverse

from laboratory.api.labview import actions
from laboratory.api.labview.tree_builder import TREE_PERMISSIONS
from laboratory.models import Object, Shelf, ShelfObject
from laboratory.tests.labview.utils import RolPermissionMixin
from laboratory.tests.utils import BaseLaboratorySetUpTest

#: ``level`` y ``label`` son literalmente la fila del roadmap.
Function = namedtuple("Function", "level label check")


class FunctionInventoryTest(RolPermissionMixin, BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.user = self.set_capabilities(self.user, list(TREE_PERMISSIONS))

        self.shelf = Shelf.objects.get(pk=1)
        self.reactive = ShelfObject.objects.filter(
            shelf=self.shelf, object__type=Object.REACTIVE
        ).first()
        self.equipment = ShelfObject.objects.create(
            object=Object.objects.filter(type=Object.EQUIPMENT).first(),
            shelf=self.shelf, quantity=1, limit_quantity=0,
            measurement_unit=self.shelf.measurement_unit,
            in_where_laboratory=self.lab,
        )

        response = self.client.get(
            reverse("laboratory:api-labview-tree-list", kwargs=self.kwargs)
        )
        # El usuario que decide las acciones tiene que ser el que salió del
        # middleware: uno leído de la base de datos no ve los permisos del Rol.
        self.request_user = response.wsgi_request.user
        tree = response.json()
        self.tree = tree
        self.room = next(
            room for room in tree["rooms"]
            if any(item["id"] == self.shelf.furniture_id for item in room["furniture"])
        )
        self.furniture = next(
            item for item in self.room["furniture"]
            if item["id"] == self.shelf.furniture_id
        )
        self.shelf_node = self.furniture["shelves"][str(self.shelf.pk)]

        page = self.client.get(
            reverse("laboratory:labview", kwargs=self.kwargs)
        ).context
        self.urls = page["labview_urls"]

    # -- utilidades --------------------------------------------------------

    def assert_is_a_qr(self, value, what):
        self.assertTrue(value, "sin QR: %s" % what)
        self.assertIn(b"<svg", base64.b64decode(value))

    def actions_for(self, shelfobject):
        return actions.get_shelfobject_actions(self.request_user, shelfobject)

    # -- una comprobación por fila del roadmap -----------------------------

    def check_room_qr(self):
        self.assert_is_a_qr(self.room["qr"], "sala")
        self.assertTrue(self.room["deep_link"].endswith("?labroom=%d" % self.room["id"]))

    def check_room_crud(self):
        for action in ("add", "change", "delete", "view"):
            self.assertIn("%s_laboratoryroom" % action, self.tree["permissions"])
        self.assertIn("counts", self.room)

    def check_furniture_qr(self):
        self.assert_is_a_qr(self.furniture["qr"], "mueble")

    def check_furniture_report(self):
        expected = reverse(
            "report:reports_furniture_detail", kwargs={"org_pk": self.org.pk}
        )
        self.assertTrue(self.furniture["report_url"].startswith(expected))
        self.assertIn("furniture=%d" % self.furniture["id"], self.furniture["report_url"])
        self.assertIn("do_report", self.tree["permissions"])

    def check_furniture_grid_and_crud(self):
        self.assertIn("cells", self.furniture["grid"])
        for field in ("name", "type", "type_name", "color"):
            self.assertIn(field, self.furniture)
        for action in ("add", "change", "delete", "view"):
            self.assertIn("%s_furniture" % action, self.tree["permissions"])

    def check_shelf_qr(self):
        self.assert_is_a_qr(self.shelf_node["qr"], "estante")

    def check_shelf_direct_link(self):
        link = self.shelf_node["deep_link"]
        for part in ("labroom=", "furniture=%d" % self.furniture["id"],
                     "shelf=%d" % self.shelf.pk):
            self.assertIn(part, link)
        # El enlace pegado en la pared y el del mapa abren lo mismo.
        self.assertEqual(self.client.get(link).status_code, 200)

    def check_shelf_fields(self):
        for field in ("color", "type_name", "discard", "measurement_unit",
                      "quantity", "infinity_quantity", "occupancy_percent",
                      "description", "counts", "position"):
            self.assertIn(field, self.shelf_node)

    def check_shelf_availability(self):
        response = self.client.get(
            reverse(
                "laboratory:api-labview-shelf-availability",
                kwargs={**self.kwargs, "pk": self.shelf.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        for field in ("total", "occupancy_percent", "measurement_unit_name",
                      "infinity_quantity", "discard"):
            self.assertIn(field, response.json())

    def check_object_detail(self):
        self.assertTrue(self.actions_for(self.reactive)["detail"])
        self.assertIn("shelfobject_details", self.urls)

    def check_object_labels(self):
        self.assertTrue(self.actions_for(self.reactive)["labels"])
        self.assertFalse(self.actions_for(self.equipment)["labels"])
        self.assertIn("recipient_list", self.urls)
        self.assertIn("generate_label", self.urls)

    def check_object_reserve(self):
        self.assertTrue(self.actions_for(self.reactive)["reserve"])

    def check_object_increase_decrease(self):
        row = self.actions_for(self.reactive)
        self.assertTrue(row["increase"] and row["decrease"])
        equipment = self.actions_for(self.equipment)
        self.assertFalse(equipment["increase"] or equipment["decrease"])

    def check_object_transfer(self):
        self.assertTrue(self.actions_for(self.reactive)["transfer_out"])

    def check_object_move_and_container(self):
        row = self.actions_for(self.reactive)
        self.assertTrue(row["move"] and row["container"])
        variants = actions.get_shelfobject_action_variants(self.reactive)
        self.assertEqual(variants["move"], "container")

    def check_object_edit_by_type(self):
        self.assertTrue(self.actions_for(self.reactive)["edit"])
        self.assertEqual(
            actions.get_shelfobject_action_variants(self.reactive)["edit"], "reactive"
        )
        self.assertFalse(self.actions_for(self.equipment)["edit"])

    def check_object_log(self):
        self.assertTrue(self.actions_for(self.reactive)["log"])
        self.assertIn("shelfobject_log", self.urls)
        self.assertIn("log", actions.LINK_ACTIONS)

    def check_object_maintenance(self):
        self.assertTrue(self.actions_for(self.equipment)["maintenance"])
        self.assertFalse(self.actions_for(self.reactive)["maintenance"])
        self.assertIn("equipment_detail", self.urls)

    def check_object_report(self):
        self.assertTrue(self.actions_for(self.reactive)["report"])
        self.assertIn("shelfobject_report", self.urls)

    def check_object_destroy(self):
        self.assertTrue(self.actions_for(self.reactive)["destroy"])

    @property
    def INVENTORY(self):
        return [
            Function("Sala", "QR propio con enlace directo", self.check_room_qr),
            Function("Sala", "Colapsar/expandir, crear, editar, borrar",
                     self.check_room_crud),
            Function("Mueble", "QR propio", self.check_furniture_qr),
            Function("Mueble", "Reporte PDF", self.check_furniture_report),
            Function("Mueble", "Cuadrícula, nombre, tipo, color; crear/editar/borrar",
                     self.check_furniture_grid_and_crud),
            Function("Estante", "QR propio", self.check_shelf_qr),
            Function("Estante", "Enlace directo (abrir en otra pestaña)",
                     self.check_shelf_direct_link),
            Function("Estante",
                     "Color, tipo, descarte, unidad, capacidad, % ocupación, límites",
                     self.check_shelf_fields),
            Function("Estante", "Disponibilidad en JSON",
                     self.check_shelf_availability),
            Function("Objeto", "Detalle con su QR y descarga",
                     self.check_object_detail),
            Function("Objeto", "Etiquetas y recipientes (SGA)",
                     self.check_object_labels),
            Function("Objeto", "Reservar", self.check_object_reserve),
            Function("Objeto", "Aumentar / disminuir",
                     self.check_object_increase_decrease),
            Function("Objeto", "Transferir a otro laboratorio",
                     self.check_object_transfer),
            Function("Objeto", "Mover de estante y gestionar contenedor",
                     self.check_object_move_and_container),
            Function("Objeto", "Editar según tipo", self.check_object_edit_by_type),
            Function("Objeto", "Bitácora y observaciones", self.check_object_log),
            Function("Objeto", "Mantenimiento, calibración, garantía, capacitación",
                     self.check_object_maintenance),
            Function("Objeto", "Descargar su reporte", self.check_object_report),
            Function("Objeto", "Borrar / desechar", self.check_object_destroy),
        ]

    def test_no_function_of_the_inventory_is_lost(self):
        for function in self.INVENTORY:
            with self.subTest("%s / %s" % (function.level, function.label)):
                function.check()

    def test_the_deep_link_contract_survives(self):
        """Los QR impresos y el mapa de peligros apuntan a este query string."""
        url = reverse("laboratory:labview", kwargs=self.kwargs)
        query = "?labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % (
            self.room["id"], self.furniture["id"], self.shelf.pk, self.reactive.pk
        )
        response = self.client.get(url + query)
        self.assertEqual(response.status_code, 200)

        resolved = response.context["search_by_url"]
        self.assertEqual(sorted(resolved), ["furniture", "labroom", "shelf",
                                            "shelfobject"])
        self.assertIn(self.room["id"], resolved["labroom"])
        self.assertIn(self.furniture["id"], resolved["furniture"]["furniture"])
        self.assertIn(self.shelf.pk, resolved["shelf"]["shelf"])
        self.assertIn(self.reactive.pk, resolved["shelfobject"]["shelfobject"])

    def test_every_capability_can_be_granted_by_an_administrator(self):
        """Una capacidad que ningún rol puede conceder es una función inalcanzable."""
        from auth_and_perms.management.commands.urlname_permissions import (
            URLNAME_PERMISSIONS,
        )

        declared = {
            entry["permission"] for entry in URLNAME_PERMISSIONS.get("labview", [])
        }
        missing = set(TREE_PERMISSIONS) - declared
        self.assertEqual(
            missing,
            set(),
            "capacidades que el árbol anuncia y ningún administrador puede conceder "
            "desde la pantalla del labview: %s" % sorted(missing),
        )
