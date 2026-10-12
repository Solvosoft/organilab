# encoding: utf-8
"""Vistas de catálogo de objetos, tablero de stock, deep links del labview,
catálogos rápidos de mobiliario y salas de laboratorio.

Cubren los caminos que el recorrido Selenium no toca: la capacidad de un material
contenedor al editarlo, las respuestas JSON de error, los 404 por laboratorio o
sala ajenos y la cadena de deep links que reconstruye el labview desde un QR.
"""

from django.urls import reverse

from laboratory.models import (
    Catalog,
    Furniture,
    LaboratoryRoom,
    MaterialCapacity,
    Object,
    ShelfObject,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest

LAB_INEXISTENTE = 999999


class ObjectUpdateMaterialTest(BaseLaboratorySetUpTest):
    """Editar un material contenedor guarda (o crea) su capacidad."""

    def setUp(self):
        super().setUp()
        self.material = Object.objects.get(pk=5)
        self.url = reverse(
            "laboratory:objectview_update",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.material.pk},
        )

    def datos(self, **extra):
        data = {
            "name": "Botella 300 ml",
            "code": "B300",
            "synonym": "Botella",
            "is_public": True,
            "type": Object.MATERIAL,
            "is_container": True,
            "capacity": 300,
            "capacity_measurement_unit": 64,
            "features": [1],
        }
        data.update(extra)
        return data

    def test_material_sin_capacidad_previa_la_crea(self):
        self.assertFalse(MaterialCapacity.objects.filter(object=self.material).exists())
        response = self.client.post(self.url, self.datos())
        self.assertEqual(response.status_code, 302)
        capacidad = MaterialCapacity.objects.get(object=self.material)
        self.assertEqual(capacidad.capacity, 300)
        self.assertEqual(capacidad.capacity_measurement_unit_id, 64)

    def test_material_con_capacidad_previa_la_actualiza(self):
        MaterialCapacity.objects.create(
            object=self.material, capacity=10, capacity_measurement_unit_id=64
        )
        response = self.client.post(self.url, self.datos(capacity=750))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MaterialCapacity.objects.filter(object=self.material).count(), 1)
        self.assertEqual(MaterialCapacity.objects.get(object=self.material).capacity, 750)

    def test_formulario_invalido_por_json_devuelve_errores(self):
        response = self.client.post(
            self.url, self.datos(capacity=""), HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("capacity", response.json())
        self.assertFalse(MaterialCapacity.objects.filter(object=self.material).exists())


class ReactiveStockDashboardTest(BaseLaboratorySetUpTest):

    def url(self, lab_pk):
        return reverse(
            "laboratory:reactive_stock_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": lab_pk},
        )

    def test_filtros_de_la_consulta_pasan_a_la_url_del_grafico(self):
        response = self.client.get(self.url(self.lab.pk), {"a": "1", "b": "2"})
        self.assertEqual(response.status_code, 200)
        url = response.context["objectlimits_url"]
        self.assertIn("?a=1&b=2", url)
        self.assertTrue(
            url.endswith("&laboratory=%d&organization=%d" % (self.lab.pk, self.org.pk))
        )

    def test_sin_filtros_solo_lleva_laboratorio_y_organizacion(self):
        response = self.client.get(self.url(self.lab.pk))
        self.assertTrue(
            response.context["objectlimits_url"].endswith(
                "?laboratory=%d&organization=%d" % (self.lab.pk, self.org.pk)
            )
        )

    def test_laboratorio_fuera_de_la_organizacion_da_404(self):
        response = self.client.get(self.url(LAB_INEXISTENTE))
        self.assertNegado(response, 404)


class LabviewDeepLinkTest(BaseLaboratorySetUpTest):
    """El deep link completa la cadena sala → mueble → estante hacia arriba."""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "laboratory:labview", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        )

    def test_mueble_solo_deduce_la_sala(self):
        furniture = Furniture.objects.filter(labroom__laboratory=self.lab).first()
        response = self.client.get(self.url, {"furniture": furniture.pk})
        self.assertEqual(response.status_code, 200)
        busqueda = response.context["search_by_url"]
        self.assertEqual(busqueda["furniture"], {"furniture": [furniture.pk]})
        self.assertEqual(busqueda["labroom"], [furniture.labroom.pk])

    def test_objeto_de_estante_solo_deduce_estante_mueble_y_sala(self):
        so = ShelfObject.objects.filter(
            shelf__furniture__labroom__laboratory=self.lab
        ).first()
        response = self.client.get(self.url, {"shelfobject": so.pk})
        self.assertEqual(response.status_code, 200)
        busqueda = response.context["search_by_url"]
        self.assertEqual(
            busqueda["shelfobject"], {"shelfobject": [so.pk], "filter_shelfobject": True}
        )
        self.assertEqual(busqueda["shelf"], {"shelf": [so.shelf.pk]})
        self.assertEqual(busqueda["furniture"], {"furniture": [so.shelf.furniture.pk]})
        self.assertEqual(busqueda["labroom"], [so.shelf.furniture.labroom.pk])


class AddCatalogTest(BaseLaboratorySetUpTest):

    def test_post_invalido_no_crea_catalogo(self):
        total = Catalog.objects.count()
        response = self.client.post(
            reverse("laboratory:add_furniture_type_catalog"), {"description": ""}
        )
        self.assertFalse(response.json()["ok"])
        self.assertEqual(Catalog.objects.count(), total)

    def test_formulario_de_tipo_de_contenedor(self):
        response = self.client.get(reverse("laboratory:add_shelf_type_catalog"))
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["title"], "New Container type")

    def test_formulario_de_estado_de_objeto_de_estante(self):
        response = self.client.get(reverse("laboratory:add_shelfobject_status"))
        data = response.json()
        self.assertEqual(data["title"], "New Shelfobject status")
        self.assertIn(reverse("laboratory:add_shelfobject_status"), data["message"])


class LabroomAislamientoTest(BaseLaboratorySetUpTest):
    """La sala 3 es del laboratorio 2: desde el laboratorio 1 no se edita ni borra."""

    def setUp(self):
        super().setUp()
        self.sala_ajena = LaboratoryRoom.objects.get(pk=3)
        self.assertNotEqual(self.sala_ajena.laboratory_id, self.lab.pk)

    def url(self, name, **kwargs):
        kwargs.update({"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        return reverse("laboratory:" + name, kwargs=kwargs)

    def test_editar_sala_de_otro_laboratorio_da_404(self):
        response = self.client.get(self.url("rooms_update", pk=self.sala_ajena.pk))
        self.assertNegado(response, 404)

    def test_editar_con_datos_invalidos_vuelve_al_formulario(self):
        sala = LaboratoryRoom.objects.get(pk=1)
        response = self.client.post(self.url("rooms_update", pk=sala.pk), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        sala.refresh_from_db()
        self.assertEqual(sala.name, "Sala de inventario")

    def test_confirmar_borrado_de_sala_ajena_da_404(self):
        response = self.client.get(self.url("rooms_delete", pk=self.sala_ajena.pk))
        self.assertNegado(response, 404)

    def test_borrar_sala_ajena_da_404_y_no_la_borra(self):
        response = self.client.post(self.url("rooms_delete", pk=self.sala_ajena.pk))
        self.assertNegado(response, 404)
        self.assertTrue(LaboratoryRoom.objects.filter(pk=self.sala_ajena.pk).exists())

    def test_regenerar_qr_en_laboratorio_fuera_de_la_organizacion_da_404(self):
        url = reverse(
            "laboratory:rebuild_laboratory_qr",
            kwargs={"org_pk": self.org.pk, "lab_pk": LAB_INEXISTENTE},
        )
        self.assertNegado(self.client.get(url), 404)
