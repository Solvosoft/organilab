# encoding: utf-8
"""El diccionario ``actions`` dice exactamente lo que la plantilla pintaba.

La pantalla vieja resuelve las acciones de cada fila con 124 líneas de botones
condicionados (``laboratory/serializers/shelfobject_actions.html``); la nueva
las manda como datos.  La traducción tiene que ser 1:1, así que aquí la
plantilla **es el oráculo**: se renderiza con el mismo contexto que usa hoy
``ShelfObjectLaboratoryViewSerializer.get_actions`` y se compara botón a botón
contra el diccionario.  Una tabla escrita a mano repetiría el mismo
razonamiento y no detectaría una divergencia real.

El ``request`` con el que se renderiza sale de una petición de verdad
(``response.wsgi_request``), para que el ``perms`` de la plantilla y el
``user.has_perm`` del diccionario lean la misma fuente: la que dejó
``ProfileMiddleware``.
"""

from django.template.loader import render_to_string
from django.urls import reverse

from laboratory.api.labview import actions
from laboratory.models import Object, Shelf, ShelfObject
from laboratory.tests.labview.utils import RolPermissionMixin
from laboratory.tests.utils import BaseLaboratorySetUpTest

#: Permisos que la plantilla consulta.  Se prueban todos juntos, ninguno, y uno
#: a uno: el caso interesante es siempre el de un permiso suelto.
RELEVANT = [
    "laboratory.change_shelfobject",
    "laboratory.delete_shelfobject",
    "laboratory.can_manage_disposal",
    "laboratory.view_shelfobject",
    "laboratory.view_shelfobjectobservation",
    "laboratory.do_report",
    "laboratory.add_tranferobject",
    "sga.view_recipientsize",
    "reservations_management.add_reservedproducts",
]


class ShelfobjectActionsEquivalenceTest(RolPermissionMixin, BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.user = self.strip_effective_permissions(self.user)

        self.shelf = Shelf.objects.get(pk=1)
        self.discard_shelf = Shelf.objects.create(
            furniture=self.shelf.furniture,
            name="Descarte",
            type=self.shelf.type,
            quantity=100,
            measurement_unit=self.shelf.measurement_unit,
            discard=True,
        )
        self.scenarios = self.build_scenarios()

    def build_scenarios(self):
        """Tipo x caja x estante de descarte, que es lo que la plantilla mira."""
        reactive = Object.objects.filter(type=Object.REACTIVE).first()
        material = Object.objects.filter(type=Object.MATERIAL).first()
        equipment = Object.objects.filter(type=Object.EQUIPMENT).first()
        unit = self.shelf.measurement_unit

        def make(obj, shelf, is_box=False):
            return ShelfObject.objects.create(
                object=obj, shelf=shelf, quantity=1, limit_quantity=0,
                measurement_unit=unit, in_where_laboratory=self.lab,
                is_box=is_box,
            )

        return {
            "reactivo": make(reactive, self.shelf),
            "reactivo en caja": make(reactive, self.shelf, is_box=True),
            "material": make(material, self.shelf),
            "equipo": make(equipment, self.shelf),
            "reactivo en estante de descarte": make(reactive, self.discard_shelf),
            "equipo en estante de descarte": make(equipment, self.discard_shelf),
        }

    # -- el oráculo --------------------------------------------------------

    def markers(self, shelfobject):
        """Qué cadena delata a cada botón en el HTML de la plantilla."""

        def url(name):
            return reverse(
                "laboratory:" + name, kwargs={**self.kwargs, "pk": shelfobject.pk}
            )

        return {
            "detail": ('id="shelfobject_view_%d"' % shelfobject.pk,),
            "labels": ("displayShelfobjectLabels(",),
            "reserve": ('data-modalid="reservesomodal"',),
            "increase": ('data-modalid="increasesomodal"',),
            "decrease": ('data-modalid="decreasesomodal"',),
            "transfer_out": ('data-modalid="transfer_out_obj_id_modal"',),
            "log": ('href="%s"' % url("get_shelfobject_log"),),
            "edit": (
                'data-modalid="edit_reactive_modal"',
                'data-modalid="edit_box_modal"',
                'data-modalid="edit_material_modal"',
            ),
            "container": ('data-modalid="managecontainermodal"',),
            "move": (
                'data-modalid="movesocontainermodal"',
                'data-modalid="movesomodal"',
            ),
            "maintenance": ('href="%s"' % url("equipment_shelfobject_detail"),),
            "report": ('href="%s"' % url("reports_shelf_objects"),),
            "destroy": ("shelfObjectDelete(",),
        }

    def oracle(self, request, shelfobject, with_shelf):
        """``{accion: bool}`` según lo que la plantilla pinta de verdad."""
        context = {
            "laboratory": self.lab,
            "org_pk": self.org,
            "shelfobject": shelfobject,
        }
        if with_shelf:
            context["shelf"] = shelfobject.shelf
        html = render_to_string(
            "laboratory/serializers/shelfobject_actions.html",
            request=request,
            context=context,
        )
        return {
            action: any(marker in html for marker in markers)
            for action, markers in self.markers(shelfobject).items()
        }

    def request_for(self, codenames):
        """Un request real, con los permisos ya puestos por el middleware."""
        self.user = self.set_capabilities(
            self.user, ["laboratory.view_laboratoryroom"] + list(codenames)
        )
        response = self.client.get(
            reverse("laboratory:api-labview-tree-list", kwargs=self.kwargs)
        )
        self.assertEqual(response.status_code, 200)
        return response.wsgi_request

    # -- pruebas -----------------------------------------------------------

    def test_the_dict_says_yes_exactly_when_the_template_paints_the_button(self):
        permission_sets = [("todos", RELEVANT), ("ninguno", [])]
        permission_sets += [(codename, [codename]) for codename in RELEVANT]

        for label, codenames in permission_sets:
            request = self.request_for(codenames)
            for name, shelfobject in self.scenarios.items():
                with self.subTest(permisos=label, escenario=name):
                    self.assertEqual(
                        actions.get_shelfobject_actions(request.user, shelfobject),
                        # La plantilla dice querer ``shelf.discard``; se le pasa
                        # el estante para preguntarle lo que quiso preguntar.
                        self.oracle(request, shelfobject, with_shelf=True),
                    )

    def test_the_documented_deviation_is_the_only_difference(self):
        """En un estante de descarte, la plantilla nunca ejecutaba su rama.

        ``shelf`` no está en el contexto que le pasa el serializer, así que
        ``{% if shelf.discard %}`` siempre era falso y borrar caía al
        ``elif delete_shelfobject``.  El diccionario usa
        ``shelfobject.shelf.discard``, que es lo que la plantilla dice querer.
        El desvío es deliberado y va en la dirección restrictiva: exige
        ``can_manage_disposal`` donde antes bastaba ``delete_shelfobject``.
        """
        request = self.request_for(["laboratory.delete_shelfobject"])
        shelfobject = self.scenarios["reactivo en estante de descarte"]

        as_rendered_today = self.oracle(request, shelfobject, with_shelf=False)
        as_data = actions.get_shelfobject_actions(request.user, shelfobject)

        differing = {
            key for key in as_data if as_data[key] != as_rendered_today[key]
        }
        self.assertEqual(differing, {"destroy"})
        self.assertTrue(as_rendered_today["destroy"])
        self.assertFalse(as_data["destroy"])

    def test_the_deviation_grants_where_the_disposal_permission_exists(self):
        request = self.request_for(["laboratory.can_manage_disposal"])
        shelfobject = self.scenarios["reactivo en estante de descarte"]
        self.assertTrue(
            actions.get_shelfobject_actions(request.user, shelfobject)["destroy"]
        )

    def test_the_variants_name_the_modal_the_template_would_open(self):
        expected = {
            "reactivo": {"edit": "reactive", "move": "container"},
            "reactivo en caja": {"edit": "box", "move": "plain"},
            "material": {"edit": "material", "move": "plain"},
            "equipo": {"edit": None, "move": "plain"},
        }
        for name, wanted in expected.items():
            with self.subTest(escenario=name):
                self.assertEqual(
                    actions.get_shelfobject_action_variants(self.scenarios[name]),
                    wanted,
                )

    def test_link_actions_are_the_ones_that_open_another_page(self):
        self.assertEqual(actions.LINK_ACTIONS, ("log", "maintenance", "report"))

    def test_the_api_row_carries_the_same_dict(self):
        request = self.request_for(RELEVANT + ["laboratory.view_shelfobject"])
        response = self.client.get(
            reverse("laboratory:api-labview-shelfobjecttable-list", kwargs=self.kwargs)
            + "?shelf=%d" % self.shelf.pk
        )
        self.assertEqual(response.status_code, 200)
        rows = {row["pk"]: row for row in response.json()["data"]}
        for name, shelfobject in self.scenarios.items():
            if shelfobject.shelf_id != self.shelf.pk:
                continue
            with self.subTest(escenario=name):
                self.assertEqual(
                    rows[shelfobject.pk]["actions"],
                    actions.get_shelfobject_actions(request.user, shelfobject),
                )

    def test_the_scenarios_actually_exercise_the_branches(self):
        """Sin esto, la equivalencia podría pasar comparando dos dicciones vacías."""
        request = self.request_for(RELEVANT)
        painted = {
            name: self.oracle(request, shelfobject, with_shelf=True)
            for name, shelfobject in self.scenarios.items()
        }

        # Con todos los permisos, cada acción se pinta al menos en un escenario.
        for action in self.markers(self.scenarios["reactivo"]):
            with self.subTest(accion=action):
                self.assertTrue(
                    any(row[action] for row in painted.values()),
                    "ningún escenario pinta %r" % action,
                )

        # Y cada escenario distingue de verdad: reactivo y equipo no coinciden.
        self.assertNotEqual(painted["reactivo"], painted["equipo"])
        self.assertNotEqual(painted["reactivo"], painted["reactivo en caja"])
        self.assertNotEqual(painted["material"], painted["equipo"])

        # Sin ningún permiso sólo queda el ojo de detalle, que no exige ninguno.
        none = self.oracle(
            self.request_for([]), self.scenarios["reactivo"], with_shelf=True
        )
        self.assertEqual({key for key, value in none.items() if value}, {"detail"})
