"""Estantes: validación de `ShelfForm`/`ShelfUpdateForm`, límites de objetos en
crear/editar y aislamiento de laboratorio al borrar.
"""

import json

from django.urls import reverse

from laboratory.models import (
    Catalog,
    Furniture,
    LaboratoryRoom,
    Laboratory,
    Object,
    OrganizationStructure,
    Shelf,
    ShelfObject,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.views.shelfs import ShelfForm, ShelfUpdateForm


class ShelfFormBase(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.unidad = Catalog.objects.get(pk=59)
        self.tipo = Catalog.objects.filter(key="container_type").first()
        self.furniture = Furniture.objects.get(pk=1)

    def datos(self, **extra):
        data = {
            "name": "Estante prueba",
            "type": self.tipo.pk,
            "furniture": self.furniture.pk,
            "color": "#73879C",
            "quantity": 10,
            "measurement_unit": self.unidad.pk,
            "description": "",
            "col": 0,
            "row": 0,
        }
        for key, value in extra.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        return data


class ShelfFormCleanTest(ShelfFormBase):

    def form(self, **extra):
        return ShelfForm(data=self.datos(**extra), org_pk=self.org.pk)

    def test_desecho_con_unidad_y_cantidad_cero_es_invalido(self):
        form = self.form(discard="on", quantity=0)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_sin_desecho_con_unidad_y_cantidad_cero_es_invalido(self):
        form = self.form(quantity=0)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_cantidad_negativa_con_infinito_es_invalida(self):
        form = self.form(quantity=-1, infinity_quantity="on")
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_sin_unidad_ni_infinito_pide_cantidad_y_unidad(self):
        form = self.form(quantity=0, measurement_unit=None)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)
        self.assertIn("measurement_unit", form.errors)

    def test_desecho_sin_unidad_ni_infinito_pide_unidad(self):
        form = self.form(discard="on", quantity=5, measurement_unit=None)
        self.assertFalse(form.is_valid())
        self.assertIn("measurement_unit", form.errors)

    def test_cantidad_no_numerica_es_error_de_formulario(self):
        form = self.form(quantity="abc")
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)


class ShelfUpdateFormCleanTest(ShelfFormBase):

    def setUp(self):
        super().setUp()
        self.vacio = Shelf.objects.create(
            furniture=self.furniture,
            name="Vacío",
            type=self.tipo,
            measurement_unit=self.unidad,
            quantity=10,
            infinity_quantity=False,
        )
        self.lleno = ShelfObject.objects.first().shelf

    def form(self, instance, **extra):
        return ShelfUpdateForm(
            data=self.datos(**extra), instance=instance, org_pk=self.org.pk
        )

    def test_sin_unidad_ni_infinito_con_cantidad_cero(self):
        form = self.form(self.vacio, quantity=0, measurement_unit=None)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)
        self.assertIn("measurement_unit", form.errors)

    def test_desecho_con_unidad_y_cantidad_valida(self):
        form = self.form(self.vacio, discard="on", quantity=5)
        self.assertTrue(form.is_valid(), form.errors)

    def test_desecho_sin_unidad_pide_unidad(self):
        form = self.form(
            self.vacio, discard="on", quantity=5, measurement_unit=None
        )
        self.assertFalse(form.is_valid())
        self.assertIn("measurement_unit", form.errors)

    def test_desecho_con_cantidad_cero_es_invalido(self):
        form = self.form(self.vacio, discard="on", quantity=0)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_cantidad_negativa_menor_a_lo_almacenado(self):
        form = self.form(
            self.lleno,
            quantity=-1,
            measurement_unit=self.lleno.measurement_unit_id or "",
        )
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_cantidad_cero_sin_objetos_conserva_el_valor(self):
        form = self.form(self.vacio, quantity=0, infinity_quantity=None)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_limite_con_otros_objetos_en_el_estante(self):
        otros = ShelfObject.objects.filter(shelf=self.lleno)
        objeto_permitido = Object.objects.exclude(
            pk__in=otros.values_list("object", flat=True)
        ).first()
        form = self.form(
            self.lleno,
            measurement_unit=self.lleno.measurement_unit_id or "",
            infinity_quantity="on",
            limit_only_objects="on",
            available_objects_when_limit=[objeto_permitido.pk],
        )
        self.assertFalse(form.is_valid())
        errores = form.errors["available_objects_when_limit"]
        for nombre in otros.values_list("object__name", flat=True).distinct():
            self.assertIn("- " + nombre, errores)

    def test_cantidad_no_numerica_es_error_de_formulario(self):
        form = self.form(self.vacio, quantity="abc")
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)


class ShelfViewsLimiteTest(ShelfFormBase):

    def post_ajax(self, url, data):
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def prefijar(self, data):
        return {"shelf--" + key: value for key, value in data.items()}

    def test_crear_estante_limitado_guarda_objetos_permitidos(self):
        objeto = Object.objects.filter(organization=self.org).first()
        url = reverse(
            "laboratory:shelf_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        data = self.prefijar(
            self.datos(
                name="Estante limitado",
                limit_only_objects="on",
                available_objects_when_limit=[objeto.pk],
            )
        )
        contenido = self.post_ajax(url, data)
        self.assertIn("<script>closeModal();</script>", json.dumps(contenido))
        shelf = Shelf.objects.get(name="Estante limitado")
        self.assertEqual(list(shelf.available_objects_when_limit.all()), [objeto])

    def test_crear_estante_invalido_devuelve_el_formulario(self):
        url = reverse(
            "laboratory:shelf_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        data = self.prefijar(self.datos(name="Sin tipo", type=None))
        contenido = self.post_ajax(url, data)
        self.assertIn("#shelfmodalbody", contenido["content"]["inner-fragments"])
        self.assertFalse(Shelf.objects.filter(name="Sin tipo").exists())

    def test_editar_estante_limitado_reemplaza_objetos_permitidos(self):
        shelf = Shelf.objects.create(
            furniture=self.furniture,
            name="Editable",
            type=self.tipo,
            measurement_unit=self.unidad,
            quantity=10,
            infinity_quantity=False,
        )
        viejo, nuevo = Object.objects.all()[:2]
        shelf.available_objects_when_limit.add(viejo)
        url = reverse(
            "laboratory:shelf_edit",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "pk": shelf.pk,
                "row": 0,
                "col": 0,
            },
        )
        data = self.prefijar(
            self.datos(
                name="Editado",
                limit_only_objects="on",
                available_objects_when_limit=[nuevo.pk],
            )
        )
        contenido = self.post_ajax(url, data)
        self.assertIn("#shelf_%s" % shelf.pk, contenido["content"]["fragments"])
        shelf.refresh_from_db()
        self.assertEqual(shelf.name, "Editado")
        self.assertEqual(list(shelf.available_objects_when_limit.all()), [nuevo])


class DeleteShelfAislamientoTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        tipo = Catalog.objects.filter(key="container_type").first()
        otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        self.lab_ajeno = Laboratory.objects.create(
            name="Lab ajeno", organization=otra_org
        )
        room = LaboratoryRoom.objects.create(name="Sala", laboratory=self.lab_ajeno)
        furniture = Furniture.objects.create(
            labroom=room,
            name="Mueble ajeno",
            type=Catalog.objects.filter(key="furniture_type").first(),
        )
        self.shelf_ajeno = Shelf.objects.create(
            furniture=furniture, name="Estante ajeno", type=tipo
        )

    def url(self, lab_pk, shelf_pk):
        return reverse(
            "laboratory:shelf_delete",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": lab_pk,
                "pk": shelf_pk,
                "row": 0,
                "col": 0,
            },
        )

    def test_no_borra_estante_de_otro_laboratorio(self):
        response = self.client.post(
            self.url(self.lab.pk, self.shelf_ajeno.pk),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(json.loads(response.content)["status"], 404)
        self.assertTrue(Shelf.objects.filter(pk=self.shelf_ajeno.pk).exists())

    def test_no_acepta_laboratorio_fuera_de_la_organizacion(self):
        response = self.client.post(
            self.url(self.lab_ajeno.pk, self.shelf_ajeno.pk),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertNotEqual(json.loads(response.content)["status"], 200)
        self.assertTrue(Shelf.objects.filter(pk=self.shelf_ajeno.pk).exists())

    def test_get_devuelve_el_script_de_confirmacion(self):
        shelf = Shelf.objects.get(name="Noveno Estante")
        url = self.url(self.lab.pk, shelf.pk)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        script = json.loads(response.content)["content"]["inner-fragments"][
            "#modalclose"
        ]
        self.assertIn('delete_shelf("#shelf_%s", "%s")' % (shelf.pk, url), script)
