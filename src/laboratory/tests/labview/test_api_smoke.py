"""Recorrido completo de la capa API del labview.

No pretende ser la matriz de permisos de la fase de pruebas: comprueba que cada
endpoint responde, que la cuadrícula irregular sobrevive a las operaciones y
que lo destructivo se niega con 409 en vez de corromper el layout.
"""

import json

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from laboratory import dataconfig
from laboratory.models import Furniture, LaboratoryRoom, Shelf, ShelfObject
from laboratory.tests.labview.utils import RolPermissionMixin
from laboratory.tests.utils import BaseLaboratorySetUpTest
from presentation.models import QRModel


class LabviewApiTest(RolPermissionMixin, BaseLaboratorySetUpTest):
    def setUp(self):
        super().setUp()
        # El usuario del fixture no trae los permisos espaciales; sin ellos
        # todo responde 403, que es justo lo que se prueba aparte.
        self.user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="laboratory",
                codename__in=[
                    "view_laboratoryroom", "add_laboratoryroom",
                    "change_laboratoryroom", "delete_laboratoryroom",
                    "view_furniture", "add_furniture", "change_furniture",
                    "delete_furniture",
                    "view_shelf", "add_shelf", "change_shelf", "delete_shelf",
                    "view_shelfobject",
                ],
            )
        )
        self.user = type(self.user).objects.get(pk=self.user.pk)
        self.client.force_login(self.user)
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.furniture = Furniture.objects.get(pk=1)
        # Una cuadrícula irregular: la forma la define el usuario.
        self.furniture.dataconfig = dataconfig.dump([[[1], [2]], [[3], [], [], []]])
        self.furniture.save()

    def url(self, name, **extra):
        return reverse("laboratory:" + name, kwargs={**self.kwargs, **extra})

    def post(self, name, payload=None, **extra):
        return self.client.post(
            self.url(name, **extra),
            data=json.dumps(payload or {}),
            content_type="application/json",
        )

    # -- árbol -------------------------------------------------------------

    def test_tree_returns_the_whole_map(self):
        response = self.client.get(self.url("api-labview-tree-list"))
        self.assertEqual(response.status_code, 200)
        tree = response.json()

        self.assertEqual(tree["laboratory"]["id"], self.lab.pk)
        self.assertTrue(tree["permissions"]["view_laboratoryroom"])
        self.assertFalse(tree["risk_enabled"])

        rooms = {room["id"]: room for room in tree["rooms"]}
        self.assertEqual(
            set(rooms),
            set(
                LaboratoryRoom.objects.filter(laboratory=self.lab).values_list(
                    "pk", flat=True
                )
            ),
        )
        furniture = [f for room in tree["rooms"] for f in room["furniture"]]
        mine = next(f for f in furniture if f["id"] == self.furniture.pk)
        # Filas irregulares: no se rellenan hasta un rectángulo.
        self.assertEqual([len(row) for row in mine["grid"]["cells"]], [2, 4])
        self.assertIn("deep_link", mine)
        self.assertIn("report_url", mine)

    def test_tree_without_risk_does_not_compute_it(self):
        tree = self.client.get(self.url("api-labview-tree-list")).json()
        room = tree["rooms"][0]
        self.assertIsNone(room["risk"])
        self.assertTrue(
            all(
                shelf["risk"] is None
                for furniture in room["furniture"]
                for shelf in furniture["shelves"].values()
            )
        )

    def test_tree_with_risk_colours_the_shelves(self):
        response = self.client.get(self.url("api-labview-tree-list") + "?risk=1")
        self.assertEqual(response.status_code, 200)
        tree = response.json()
        self.assertTrue(tree["risk_enabled"])
        room = tree["rooms"][0]
        self.assertIsNotNone(room["risk"])
        shelves = [
            shelf
            for furniture in room["furniture"]
            for shelf in furniture["shelves"].values()
        ]
        self.assertTrue(shelves)
        self.assertTrue(all(shelf["risk"] is not None for shelf in shelves))

    def test_the_tree_carries_everything_the_old_card_painted(self):
        """La tarjeta de estante antigua pintaba mas que nombre y ocupacion.

        `shelf_card.html` mostraba el pk delante del nombre, el color propio del
        estante y su descripcion; si el arbol no los manda, la vista nueva no
        puede pintarlos y esa informacion se pierde.
        """
        shelf = Shelf.objects.get(pk=1)
        shelf.description = "<b>Reactivos organicos</b>"
        shelf.save()

        tree = self.client.get(self.url("api-labview-tree-list")).json()
        painted = None
        for room in tree["rooms"]:
            for furniture in room["furniture"]:
                if str(shelf.pk) in furniture["shelves"]:
                    painted = furniture["shelves"][str(shelf.pk)]
        self.assertIsNotNone(painted)
        self.assertEqual(painted["description"], "<b>Reactivos organicos</b>")
        self.assertEqual(painted["color"], shelf.color)
        self.assertEqual(painted["id"], shelf.pk)
        self.assertIn("qr", painted)
        self.assertIn("deep_link", painted)

    def test_the_tree_materialises_missing_qr_codes(self):
        """La plantilla antigua creaba el QR al vuelo si no existía.

        Si el árbol solo leyera los ya guardados, una sala o un estante recién
        creados se quedarían sin QR y el usuario perdería una función que hoy
        tiene sin pedir nada.
        """
        content_type = ContentType.objects.get_for_model(LaboratoryRoom)
        QRModel.objects.filter(content_type=content_type).delete()

        tree = self.client.get(self.url("api-labview-tree-list")).json()
        self.assertTrue(tree["rooms"])
        for room in tree["rooms"]:
            self.assertTrue(room["qr"], "la sala %s se quedo sin QR" % room["id"])
        self.assertTrue(
            QRModel.objects.filter(content_type=content_type).exists()
        )

    # -- CRUDs -------------------------------------------------------------

    def test_labroom_crud(self):
        response = self.post("api-labview-labroom-list", {"name": "Sala nueva"})
        self.assertEqual(response.status_code, 201)
        pk = LaboratoryRoom.objects.get(name="Sala nueva").pk

        response = self.client.put(
            self.url("api-labview-labroom-detail", pk=pk),
            data=json.dumps({"name": "Sala renombrada"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(LaboratoryRoom.objects.filter(name="Sala renombrada").exists())

        response = self.client.delete(self.url("api-labview-labroom-detail", pk=pk))
        self.assertEqual(response.status_code, 204)

    def test_furniture_cannot_be_created_in_another_laboratory(self):
        other = LaboratoryRoom.objects.exclude(laboratory=self.lab).first()
        self.assertIsNotNone(other)
        response = self.client.post(
            self.url("api-labview-furniture-list") + "?labroom=%d" % other.pk,
            data=json.dumps({"name": "Intruso", "type": self.furniture.type_id}),
            content_type="application/json",
        )
        # El padre se acota al laboratorio de la URL, así que nombrar el pk de
        # otro laboratorio no existe.
        self.assertEqual(response.status_code, 404)

    def test_shelf_is_created_already_placed(self):
        response = self.client.post(
            self.url("api-labview-shelf-list") + "?furniture=%d" % self.furniture.pk,
            data=json.dumps(
                {
                    "name": "Estante nuevo",
                    "type": Shelf.objects.first().type_id,
                    "quantity": 10,
                    "measurement_unit": Shelf.objects.first().measurement_unit_id,
                    "infinity_quantity": False,
                    "row": 1,
                    "col": 2,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        pk = response.json()["id"]
        # La posición nace con el estante: no hay ventana en la que quede
        # huérfano esperando a que alguien guarde el mueble.
        self.furniture.refresh_from_db()
        self.assertEqual(dataconfig.get_position(self.furniture.get_grid(), pk), (1, 2))

    def test_shelf_move_uses_the_pk_not_dom_indexes(self):
        response = self.client.put(
            self.url("api-labview-shelf-move", pk=3),
            data=json.dumps({"row": 0, "col": 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.furniture.refresh_from_db()
        self.assertEqual(dataconfig.get_position(self.furniture.get_grid(), 3), (0, 1))

    def test_shelf_with_objects_cannot_be_deleted(self):
        shelf = Shelf.objects.get(pk=1)
        self.assertTrue(ShelfObject.objects.filter(shelf=shelf).exists())
        response = self.client.delete(self.url("api-labview-shelf-detail", pk=shelf.pk))
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Shelf.objects.filter(pk=shelf.pk).exists())

    def test_shelf_availability_is_json(self):
        response = self.client.get(self.url("api-labview-shelf-availability", pk=1))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("occupancy_percent", data)
        self.assertIn("measurement_unit_name", data)

    # -- cuadrícula --------------------------------------------------------

    def test_add_row_keeps_the_shape(self):
        response = self.post("api-labview-furniture-add-row", pk=self.furniture.pk)
        self.assertEqual(response.status_code, 200)
        cells = response.json()["grid"]["cells"]
        # La fila nueva es tan ancha como la más larga, y las demás no cambian.
        self.assertEqual([len(row) for row in cells], [2, 4, 4])

    def test_add_col_preserves_irregularity(self):
        response = self.post("api-labview-furniture-add-col", pk=self.furniture.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [len(row) for row in response.json()["grid"]["cells"]], [3, 5]
        )

    def test_removing_an_occupied_row_is_refused(self):
        response = self.post(
            "api-labview-furniture-remove-row", {"index": 0}, pk=self.furniture.pk
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("shelves", response.json())
        self.furniture.refresh_from_db()
        self.assertEqual(
            [len(row) for row in self.furniture.get_grid()], [2, 4]
        )

    def test_removing_an_empty_column_works(self):
        response = self.post(
            "api-labview-furniture-remove-col", {"index": 3}, pk=self.furniture.pk
        )
        self.assertEqual(response.status_code, 200)
        # Solo encoge la fila que tenía esa columna.
        self.assertEqual([len(row) for row in response.json()["grid"]["cells"]], [2, 3])

    def test_furniture_retrieve_carries_the_grid(self):
        """Lo que el editor pide para repintarse tras cada operacion.

        Recargar el arbol entero rehace el mapa y destruiria la instancia del
        widget en plena edicion, asi que el mueble tiene que poder devolver su
        estado solo.
        """
        response = self.client.get(
            self.url("api-labview-furniture-detail", pk=self.furniture.pk)
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([len(row) for row in data["grid"]["cells"]], [2, 4])
        self.assertIn("shelves", data)
        self.assertIn("name", data)

    # -- tabla -------------------------------------------------------------

    def test_shelfobject_table_sends_actions_as_data(self):
        response = self.client.get(
            self.url("api-labview-shelfobjecttable-list") + "?shelf=1"
        )
        self.assertEqual(response.status_code, 200)
        rows = response.json()["data"]
        self.assertTrue(rows)
        actions = rows[0]["actions"]
        self.assertIsInstance(actions, dict)
        for name in [
            "detail", "labels", "reserve", "increase", "decrease", "transfer_out",
            "log", "edit", "container", "move", "maintenance", "report", "destroy",
        ]:
            self.assertIn(name, actions)
            self.assertIsInstance(actions[name], bool)

    def test_the_row_carries_what_the_modals_read(self):
        """Los modales reutilizados leen `data-*` que salen de estos campos.

        Sin `container_display` el select de contenedor pierde la cantidad y la
        unidad; sin `reactive_expiration_date` el aviso de caducidad de una
        caja se queda sin fecha; sin `quantity_units` el modal de restar no
        sabe cuantas cajas hay.
        """
        response = self.client.get(
            self.url("api-labview-shelfobjecttable-list") + "?shelf=1"
        )
        row = response.json()["data"][0]
        for field in [
            "object_raw_name", "container_id", "container_display",
            "reactive_expiration_date", "quantity_units", "is_box", "shelf",
            "type", "variants",
        ]:
            self.assertIn(field, row, field)

        shelfobject = ShelfObject.objects.get(pk=row["pk"])
        if shelfobject.container:
            # El __str__ completo, no solo el nombre del objeto: es lo que
            # pintaba la plantilla antigua.
            self.assertEqual(row["container_display"], str(shelfobject.container))

    def test_the_row_keeps_the_translated_labels(self):
        """Tipo, nombre, cantidad y unidad estaban traducidos y deben seguirlo.

        Se heredan del serializer de la vista antigua justo para que no puedan
        divergir.
        """
        from laboratory.api.serializers import ShelfObjectLaboratoryViewSerializer
        from laboratory.api.labview.serializers import LabviewShelfObjectSerializer

        for name in ["get_object_type", "get_object_name", "get_unit", "get_quantity"]:
            self.assertIs(
                getattr(LabviewShelfObjectSerializer, name),
                getattr(ShelfObjectLaboratoryViewSerializer, name),
                "%s dejo de heredarse y puede perder la traduccion" % name,
            )

    # -- permisos ----------------------------------------------------------

    def test_every_endpoint_refuses_a_user_without_permissions(self):
        # En organilab los permisos efectivos no salen de ``user_permissions``:
        # los inyecta ``ProfileMiddleware`` desde el Rol que el perfil tiene en
        # esa organizacion y ese laboratorio. Vaciar solo los directos dejaria
        # pasar al usuario y la prueba mentiria.
        self.user = self.strip_effective_permissions(self.user)

        self.assertEqual(
            self.client.get(self.url("api-labview-tree-list")).status_code, 403
        )
        self.assertEqual(
            self.client.get(
                self.url("api-labview-shelfobjecttable-list") + "?shelf=1"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.post("api-labview-labroom-list", {"name": "x"}).status_code, 403
        )
        self.assertEqual(
            self.post(
                "api-labview-furniture-add-row", pk=self.furniture.pk
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(
                self.url("api-labview-shelf-detail", pk=1)
            ).status_code,
            403,
        )
