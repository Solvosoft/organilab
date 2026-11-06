"""Ramas de ``academic/views.py`` que el resto de la suite no ejercita.

Se cubren con el cliente de pruebas de Django: reservas generadas desde un
procedimiento (con y sin cajas), el guardado del formulario Formio de "mis
procedimientos" y los esquemas inválidos al crear o editar un paso.
"""

import copy

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from academic.models import (
    MyProcedure,
    Procedure,
    ProcedureRequiredObject,
    ProcedureStep,
)
from laboratory.models import BaseUnitValues, Catalog, Laboratory, ShelfObject
from reservations_management.models import ReservedProducts

FECHA_INICIAL = "17/01/2023 11:02:05"
FECHA_FINAL = "22/01/2023 11:02:05"


class ReservaDesdeProcedimientoTest(TestCase):
    """``generate_reservation`` reparte lo requerido entre los objetos del laboratorio."""

    fixtures = ["object.json", "procedure.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.lab = Laboratory.objects.get(pk=1)
        self.procedure = Procedure.objects.get(pk=10)
        ProcedureRequiredObject.objects.all().delete()
        # Plantilla fuera del laboratorio: `in_where_laboratory` vacío, no cuenta.
        self.base = ShelfObject.objects.get(pk=2)
        ShelfObject.objects.filter(object=self.base.object).exclude(pk=self.base.pk).delete()
        self.url = reverse(
            "academic:generate_reservation", kwargs={"org_pk": 1, "lab_pk": self.lab.pk}
        )

    def requerir(self, cantidad):
        return ProcedureRequiredObject.objects.create(
            step=ProcedureStep.objects.get(pk=17),
            object=self.base.object,
            quantity=cantidad,
            measurement_unit=self.base.measurement_unit,
        )

    def objeto_en_estante(self, quantity=1, **kwargs):
        shelf_object = copy.copy(self.base)
        shelf_object.pk = None
        shelf_object.quantity = quantity
        shelf_object.in_where_laboratory = self.lab
        for field, value in kwargs.items():
            setattr(shelf_object, field, value)
        shelf_object.save()
        return shelf_object

    def caja(self, unidades_por_caja, cajas):
        return self.objeto_en_estante(
            is_box=True,
            units_per_box=unidades_por_caja,
            quantity_units=[
                {"code": codigo, "units": unidades} for codigo, unidades in cajas
            ],
        )

    def reservar(self):
        return self.client.post(
            self.url,
            {
                "procedure": self.procedure.pk,
                "initial_date": FECHA_INICIAL,
                "final_date": FECHA_FINAL,
            },
        )

    def test_sin_cajas_reparte_entre_estantes_de_menor_a_mayor(self):
        self.requerir(10)
        cuatro = self.objeto_en_estante(4)
        ocho = self.objeto_en_estante(8)
        veinte = self.objeto_en_estante(20)

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["state"])
        reservado = dict(
            ReservedProducts.objects.values_list("shelf_object", "amount_required")
        )
        self.assertEqual(reservado, {cuatro.pk: 4, ocho.pk: 6})
        self.assertNotIn(veinte.pk, reservado)

    def test_con_cajas_completas_y_fraccion(self):
        self.requerir(25)
        primera = self.caja(10, [("A", 10), ("B", 10), ("C", 5)])
        segunda = self.caja(10, [("D", 10)])

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva = ReservedProducts.objects.get()
        self.assertEqual(reserva.shelf_object, primera)
        self.assertEqual(reserva.amount_required, 2.5)
        self.assertEqual(
            reserva.reserved_boxes,
            [
                {"code": "A", "units": 10},
                {"code": "B", "units": 10},
                {"code": "C", "units": 5},
            ],
        )
        self.assertFalse(ReservedProducts.objects.filter(shelf_object=segunda).exists())

    def test_cajas_insuficientes_rechazan_la_reserva(self):
        self.requerir(100)
        self.caja(10, [("A", 10)])

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(str(self.base.object), response.json()["msg"])
        self.assertFalse(ReservedProducts.objects.exists())

    def test_fraccion_de_caja_salta_estantes_sin_caja_suficiente(self):
        self.requerir(3)
        sin_caja_util = self.caja(10, [("X", 2)])
        con_caja = self.caja(10, [("Y", 10)])

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva = ReservedProducts.objects.get()
        self.assertEqual(reserva.shelf_object, con_caja)
        self.assertEqual(reserva.reserved_boxes, [{"code": "Y", "units": 3}])
        self.assertFalse(
            ReservedProducts.objects.filter(shelf_object=sin_caja_util).exists()
        )

    def test_fraccion_que_redondea_por_encima_de_la_caja_disponible(self):
        """2.5 unidades piden una caja con 3 (se redondea hacia arriba): 2.6 no alcanza."""
        self.requerir(2.5)
        corta = self.caja(10, [("X", 2.6)])
        con_caja = self.caja(10, [("Y", 10)])

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva = ReservedProducts.objects.get()
        self.assertEqual(reserva.shelf_object, con_caja)
        self.assertEqual(reserva.reserved_boxes, [{"code": "Y", "units": 3}])
        self.assertFalse(ReservedProducts.objects.filter(shelf_object=corta).exists())

    def test_cajas_vacias_o_solo_parciales_no_reservan(self):
        self.requerir(10)
        vacia = self.caja(5, [("V", 0)])
        parciales = self.caja(10, [("P", 5), ("Q", 5)])
        llena = self.caja(10, [("L", 10)])

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva = ReservedProducts.objects.get()
        self.assertEqual(reserva.shelf_object, llena)
        self.assertEqual(reserva.reserved_boxes, [{"code": "L", "units": 10}])
        self.assertFalse(
            ReservedProducts.objects.filter(shelf_object__in=[vacia, parciales]).exists()
        )


class ReservaPorFamiliaDeUnidadTest(ReservaDesdeProcedimientoTest):
    """Sin cajas, lo pedido se compara y reparte en unidad base dentro de la familia."""

    def setUp(self):
        super().setUp()
        litros = Catalog.objects.create(key="units", description="Litros prueba")
        self.litros = litros
        self.mililitros = Catalog.objects.create(key="units", description="Mililitros prueba")
        BaseUnitValues.objects.create(measurement_unit=litros, measurement_unit_base=litros, si_value=1)
        BaseUnitValues.objects.create(
            measurement_unit=self.mililitros, measurement_unit_base=litros, si_value=1000
        )

    def requerir_en(self, cantidad, unidad):
        requerido = self.requerir(cantidad)
        requerido.measurement_unit = unidad
        requerido.save()
        return requerido

    def test_pide_mililitros_y_hay_litros(self):
        self.requerir_en(500, self.mililitros)
        litro = self.objeto_en_estante(1, measurement_unit=self.litros)

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva = ReservedProducts.objects.get()
        self.assertEqual(reserva.shelf_object, litro)
        # Se descuenta de la existencia, así que va en su unidad (litros).
        self.assertAlmostEqual(reserva.amount_required, 0.5)

    def test_reparte_entre_unidades_de_la_familia(self):
        self.requerir_en(1.5, self.litros)
        medio = self.objeto_en_estante(500, measurement_unit=self.mililitros)
        litro = self.objeto_en_estante(1, measurement_unit=self.litros)

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservado = dict(ReservedProducts.objects.values_list("shelf_object", "amount_required"))
        self.assertAlmostEqual(reservado[medio.pk], 500)
        self.assertAlmostEqual(reservado[litro.pk], 1)

    def test_familia_insuficiente_rechaza(self):
        self.requerir_en(2, self.litros)
        self.objeto_en_estante(500, measurement_unit=self.mililitros)
        self.objeto_en_estante(1, measurement_unit=self.litros)

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ReservedProducts.objects.exists())

    def test_otra_familia_no_cuenta(self):
        kilos = Catalog.objects.create(key="units", description="Kilogramos prueba")
        BaseUnitValues.objects.create(measurement_unit=kilos, measurement_unit_base=kilos, si_value=1)
        self.requerir_en(1, self.litros)
        self.objeto_en_estante(5, measurement_unit=kilos)

        response = self.reservar()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProcedimientoSinObjetosTest(TestCase):
    fixtures = ["object.json", "procedure.json"]

    def setUp(self):
        self.client.force_login(User.objects.get(pk=1))

    def test_get_procedure_sin_objetos_responde_400(self):
        ProcedureRequiredObject.objects.all().delete()
        response = self.client.get(
            reverse("academic:get_procedure", kwargs={"org_pk": 1, "pk": 10})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["pk"], 10)
        self.assertTrue(response.json()["msg"])


class EsquemaDePasoInvalidoTest(TestCase):
    """Un ``form_schema`` que no es un objeto JSON no crea formulario ni rompe la vista."""

    fixtures = ["object.json", "procedure.json"]

    def setUp(self):
        self.client.force_login(User.objects.get(pk=1))
        self.procedure = Procedure.objects.get(pk=10)

    def crear_paso(self, form_schema):
        return self.client.post(
            reverse("academic:procedure_step", kwargs={"org_pk": 1, "pk": 10}),
            {"title": "Paso nuevo", "description": "desc", "form_schema": form_schema},
        )

    def editar_paso(self, step, form_schema):
        return self.client.post(
            reverse("academic:update_step", kwargs={"org_pk": 1, "pk": step.pk}),
            {"title": "Paso editado", "description": "desc", "form_schema": form_schema},
        )

    def test_crear_paso_con_json_invalido(self):
        response = self.crear_paso("{no es json")
        self.assertEqual(response.status_code, 302)
        step = ProcedureStep.objects.get(title="Paso nuevo")
        self.assertIsNone(step.form)

    def test_crear_paso_con_json_que_no_es_objeto(self):
        response = self.crear_paso("[1, 2]")
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(ProcedureStep.objects.get(title="Paso nuevo").form)

    def test_editar_paso_con_json_invalido(self):
        step = ProcedureStep.objects.get(pk=17)
        response = self.editar_paso(step, "{no es json")
        self.assertEqual(response.status_code, 302)
        step.refresh_from_db()
        self.assertEqual(step.title, "Paso editado")
        self.assertIsNone(step.form)

    def test_editar_paso_con_json_que_no_es_objeto(self):
        step = ProcedureStep.objects.get(pk=17)
        response = self.editar_paso(step, '"texto"')
        self.assertEqual(response.status_code, 302)
        step.refresh_from_db()
        self.assertIsNone(step.form)


class CompletarMiProcedimientoTest(TestCase):
    fixtures = ["object.json", "my_procedure.json"]

    def setUp(self):
        self.client.force_login(User.objects.get(pk=1))
        self.my_procedure = MyProcedure.objects.get(pk=1)
        self.url = reverse(
            "academic:complete_my_procedure",
            kwargs={"org_pk": 1, "lab_pk": 1, "pk": self.my_procedure.pk},
        )

    def url_alta(self):
        return reverse(
            "academic:add_my_procedures",
            kwargs={
                "org_pk": 1,
                "lab_pk": 1,
                "content_type": "laboratory",
                "model": "laboratory",
            },
        )

    def test_get_del_formulario_de_alta_no_crea_procedimientos(self):
        """Un GET solo muestra la página: antes creaba un procedimiento vacío."""
        total = MyProcedure.objects.count()
        response = self.client.get(self.url_alta())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "academic/procedure.html")
        self.assertEqual(MyProcedure.objects.count(), total)

    def test_alta_con_plantilla_inexistente_no_crea(self):
        total = MyProcedure.objects.count()
        response = self.client.post(
            self.url_alta(), {"name": "Sin plantilla", "custom_procedure": 99999}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "academic/procedure.html")
        self.assertEqual(MyProcedure.objects.count(), total)

    def test_guardar_paso_con_json_invalido_no_modifica_el_esquema(self):
        self.my_procedure.schema = {"steps_data": {"17": {"previo": 1}}}
        self.my_procedure.save()
        response = self.client.post(
            self.url,
            {"save_step_form": "1", "step_pk": "17", "step_form_data": "{roto"},
        )
        self.assertEqual(response.json(), {"status": "ok"})
        self.my_procedure.refresh_from_db()
        self.assertEqual(self.my_procedure.schema["steps_data"], {"17": {"previo": 1}})

    def test_enviar_formulario_actualiza_los_valores_por_defecto(self):
        self.my_procedure.schema = {
            "components": [
                {"key": "texto", "type": "textfield", "defaultValue": ""},
                {"key": "opcion", "type": "select", "defaultValue": ""},
                {"key": "casillas", "type": "selectboxes", "defaultValue": {}},
                {"key": "intacto", "type": "textfield", "defaultValue": "igual"},
                {
                    "key": "tabla",
                    "type": "table",
                    "rows": [[{"key": "celda", "type": "textfield", "defaultValue": ""}]],
                },
            ]
        }
        self.my_procedure.save()

        response = self.client.post(
            self.url,
            {
                "csrfmiddlewaretoken": "x",
                "status": "Finalized",
                "data[texto]": "hola",
                "data[opcion]": ["a", "b"],
                "data[casillas]": ["x", "y"],
                "data[celda]": "valor",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url", response.json())
        self.my_procedure.refresh_from_db()
        componentes = {c["key"]: c for c in self.my_procedure.schema["components"]}
        self.assertEqual(self.my_procedure.status, "Finalized")
        self.assertEqual(componentes["texto"]["defaultValue"], "hola")
        self.assertEqual(componentes["opcion"]["defaultValue"], ["a", "b"])
        self.assertEqual(componentes["casillas"]["defaultValue"], {"x": True, "y": True})
        self.assertEqual(componentes["intacto"]["defaultValue"], "igual")
        self.assertEqual(componentes["tabla"]["rows"][0][0]["defaultValue"], "valor")
