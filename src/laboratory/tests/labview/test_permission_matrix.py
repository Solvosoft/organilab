# encoding: utf-8
"""Matriz de permisos del labview: mostrar y autorizar son dos cosas.

La interfaz se pinta con lo que el payload autoriza (el bloque ``permissions``
del árbol y el diccionario ``actions`` de cada fila), y cada endpoint vuelve a
exigir su permiso.  Estas pruebas comprueban las dos capas a la vez y que dicen
lo mismo: una capacidad que el árbol anuncia tiene que existir en el endpoint,
y una que niega tiene que responder 403 aunque el cliente la invoque igual.

Los permisos se manipulan **sólo** por ``RolPermissionMixin``; el porqué está
en ``laboratory/tests/labview/utils.py``.
"""

import json
from collections import namedtuple

from django.db import transaction
from django.urls import reverse

from laboratory import dataconfig
from laboratory.api.labview.tree_builder import TREE_PERMISSIONS
from laboratory.models import Furniture, LaboratoryRoom, Shelf
from laboratory.tests.labview.utils import RolPermissionMixin
from laboratory.tests.utils import BaseLaboratorySetUpTest

#: Sin esto no se puede ni pedir el árbol, así que acompaña a cada capacidad
#: bajo prueba en vez de contarse como una más.
BASELINE = ["laboratory.view_laboratoryroom"]

#: Una fila por capacidad.  ``probe`` es ``None`` cuando la capacidad sólo vive
#: en el payload (decide qué pinta la interfaz) y no tiene endpoint propio en
#: el labview: su endpoint real está en otra app o en otra pantalla.
Capability = namedtuple("Capability", "codename probe")


class LabviewPermissionMatrixTest(RolPermissionMixin, BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.furniture = Furniture.objects.get(pk=1)
        self.furniture.dataconfig = dataconfig.dump([[[1], [2]], [[3], [], [], []]])
        self.furniture.save()
        self.labroom = LaboratoryRoom.objects.get(pk=self.furniture.labroom_id)
        self.shelf = Shelf.objects.get(pk=3)
        self.user = self.strip_effective_permissions(self.user)

    # -- utilidades --------------------------------------------------------

    def url(self, name, **extra):
        return reverse("laboratory:" + name, kwargs={**self.kwargs, **extra})

    def post(self, name, payload=None, query="", **extra):
        return self.client.post(
            self.url(name, **extra) + query,
            data=json.dumps(payload or {}),
            content_type="application/json",
        )

    # -- sondas: una petición real por capacidad ---------------------------

    def probe_tree(self):
        return self.client.get(self.url("api-labview-tree-list"))

    def probe_add_room(self):
        return self.post("api-labview-labroom-list", {"name": "Sala nueva"})

    def probe_change_room(self):
        return self.client.patch(
            self.url("api-labview-labroom-detail", pk=self.labroom.pk),
            data=json.dumps({"name": "Otra"}),
            content_type="application/json",
        )

    def probe_delete_room(self):
        room = LaboratoryRoom.objects.create(
            name="Vacía", laboratory=self.lab, created_by=self.user
        )
        return self.client.delete(
            self.url("api-labview-labroom-detail", pk=room.pk)
        )

    def probe_view_furniture(self):
        return self.client.get(
            self.url("api-labview-furniture-detail", pk=self.furniture.pk)
        )

    def probe_add_furniture(self):
        return self.post(
            "api-labview-furniture-list",
            {"name": "Mueble", "type": self.furniture.type_id, "color": "#fff"},
            query="?labroom=%d" % self.labroom.pk,
        )

    def probe_change_furniture(self):
        return self.post(
            "api-labview-furniture-add-row", {"index": 0}, pk=self.furniture.pk
        )

    def probe_delete_furniture(self):
        furniture = Furniture.objects.create(
            labroom=self.labroom, name="Suelto", type=self.furniture.type,
            dataconfig="[[[]]]",
        )
        return self.client.delete(
            self.url("api-labview-furniture-detail", pk=furniture.pk)
        )

    def probe_view_shelf(self):
        return self.client.get(
            self.url("api-labview-shelf-availability", pk=self.shelf.pk)
        )

    def probe_add_shelf(self):
        return self.post(
            "api-labview-shelf-list",
            {
                "name": "Estante",
                "type": self.shelf.type_id,
                "quantity": 10,
                "measurement_unit": self.shelf.measurement_unit_id,
                "infinity_quantity": False,
                "row": 1,
                "col": 3,
            },
            query="?furniture=%d" % self.furniture.pk,
        )

    def probe_change_shelf(self):
        return self.client.put(
            self.url("api-labview-shelf-move", pk=self.shelf.pk),
            data=json.dumps({"row": 1, "col": 1}),
            content_type="application/json",
        )

    def probe_delete_shelf(self):
        shelf = Shelf.objects.create(
            furniture=self.furniture, name="Vacío", type=self.shelf.type,
            quantity=1, measurement_unit=self.shelf.measurement_unit,
        )
        return self.client.delete(self.url("api-labview-shelf-detail", pk=shelf.pk))

    def probe_view_shelfobject(self):
        return self.client.get(
            self.url("api-labview-shelfobjecttable-list") + "?shelf=1"
        )

    CAPABILITIES = [
        Capability("laboratory.view_laboratoryroom", "probe_tree"),
        Capability("laboratory.add_laboratoryroom", "probe_add_room"),
        Capability("laboratory.change_laboratoryroom", "probe_change_room"),
        Capability("laboratory.delete_laboratoryroom", "probe_delete_room"),
        Capability("laboratory.view_furniture", "probe_view_furniture"),
        Capability("laboratory.add_furniture", "probe_add_furniture"),
        Capability("laboratory.change_furniture", "probe_change_furniture"),
        Capability("laboratory.delete_furniture", "probe_delete_furniture"),
        Capability("laboratory.view_shelf", "probe_view_shelf"),
        Capability("laboratory.add_shelf", "probe_add_shelf"),
        Capability("laboratory.change_shelf", "probe_change_shelf"),
        Capability("laboratory.delete_shelf", "probe_delete_shelf"),
        Capability("laboratory.view_shelfobject", "probe_view_shelfobject"),
        # Sólo payload: deciden qué pinta la interfaz, y su endpoint vive en
        # otra pantalla (bitácora, reportes, etiquetas, reservas, traslados).
        Capability("laboratory.add_shelfobject", None),
        Capability("laboratory.change_shelfobject", None),
        Capability("laboratory.delete_shelfobject", None),
        Capability("laboratory.view_shelfobjectobservation", None),
        Capability("laboratory.can_manage_disposal", None),
        Capability("laboratory.do_report", None),
        Capability("laboratory.add_tranferobject", None),
        Capability("sga.view_recipientsize", None),
        Capability("sga.add_recipientsize", None),
        Capability("reservations_management.add_reservedproducts", None),
    ]

    # -- el bloque ``permissions`` del árbol -------------------------------

    def test_the_table_covers_every_capability_the_tree_announces(self):
        """Si alguien añade una capacidad al árbol, esta matriz tiene que verla."""
        self.assertEqual(
            sorted(capability.codename for capability in self.CAPABILITIES),
            sorted(TREE_PERMISSIONS),
        )

    def test_the_tree_announces_exactly_the_capabilities_the_user_has(self):
        expected_keys = {code.split(".", 1)[1] for code in TREE_PERMISSIONS}
        for capability in self.CAPABILITIES:
            with self.subTest(capability=capability.codename), transaction.atomic():
                self.user = self.set_capabilities(
                    self.user, BASELINE + [capability.codename]
                )
                announced = self.probe_tree().json()["permissions"]

                self.assertEqual(set(announced), expected_keys)
                granted = {key for key, value in announced.items() if value}
                self.assertEqual(
                    granted,
                    {
                        code.split(".", 1)[1]
                        for code in set(BASELINE) | {capability.codename}
                    },
                )
                transaction.set_rollback(True)

    # -- los endpoints -----------------------------------------------------

    def test_every_endpoint_refuses_without_its_capability(self):
        for capability in self.CAPABILITIES:
            if capability.probe is None:
                continue
            with self.subTest(capability=capability.codename), transaction.atomic():
                # Con todas las demás capacidades menos la suya: así el 403 sólo
                # puede venir de la que falta.
                others = [
                    other.codename
                    for other in self.CAPABILITIES
                    if other.codename != capability.codename
                ]
                self.user = self.set_capabilities(self.user, others)
                response = getattr(self, capability.probe)()
                self.assertEqual(response.status_code, 403, capability.codename)
                transaction.set_rollback(True)

    def test_every_endpoint_stops_refusing_with_its_capability(self):
        for capability in self.CAPABILITIES:
            if capability.probe is None:
                continue
            with self.subTest(capability=capability.codename), transaction.atomic():
                self.user = self.set_capabilities(
                    self.user, BASELINE + [capability.codename]
                )
                response = getattr(self, capability.probe)()
                self.assertNotEqual(response.status_code, 403, capability.codename)
                transaction.set_rollback(True)

    # -- que la matriz no mienta -------------------------------------------

    def test_the_capability_comes_from_the_rol_and_not_from_user_permissions(self):
        """La prueba que evita que toda la clase pase por la razón equivocada."""
        self.user = self.set_capabilities(
            self.user, BASELINE + ["laboratory.add_laboratoryroom"]
        )
        self.assertEqual(self.user.user_permissions.count(), 0)
        self.assertEqual(self.probe_add_room().status_code, 201)

        self.user = self.strip_effective_permissions(self.user)
        self.assertEqual(self.probe_add_room().status_code, 403)

    def test_an_action_without_a_declared_permission_would_be_refused(self):
        """``AllPermissionByAction`` responde 403 a una acción no mapeada.

        Es fail-closed, que está bien, pero convierte «olvidar una entrada en
        ``perms``» en una función que desaparece de la pantalla sin ningún
        error visible.  Aquí se comprueba que no falta ninguna.
        """
        from laboratory.api.labview import viewsets

        managed = [
            viewsets.LabRoomManagement,
            viewsets.FurnitureManagement,
            viewsets.ShelfManagement,
            viewsets.LabviewTreeViewSet,
            viewsets.LabviewShelfObjectTableViewSet,
        ]
        standard = (
            "list", "retrieve", "create", "update", "partial_update", "destroy",
        )
        for viewset in managed:
            with self.subTest(viewset=viewset.__name__):
                actions = {name for name in standard if hasattr(viewset, name)}
                # Sólo las acciones que declara el labview: las heredadas de la
                # biblioteca y que aquí no se usan responden 403, que es el
                # comportamiento correcto y no un permiso que falte.
                actions |= {
                    action.__name__
                    for action in viewset.get_extra_actions()
                    if action.__module__.startswith("laboratory.api.labview")
                }
                self.assertEqual(
                    actions - set(viewset.perms),
                    set(),
                    "acciones sin permiso declarado en %s" % viewset.__name__,
                )
