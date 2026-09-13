from unittest import mock

from django.test import TestCase
from django.utils import timezone

from laboratory.models import (
    Catalog,
    Laboratory,
    Object,
    Shelf,
    ShelfObject,
    ShelfObjectCodeCounter,
)
from sga.models import Substance, SubstanceCharacteristics, SubstanceLaboratory


class ShelfObjectLotCodeTest(TestCase):
    """El lote que completa el código de la etiqueta al crear el envase.

    La primera mitad la emite la aprobación de la sustancia; aquí se comprueba la
    segunda: año, mes y consecutivo por sustancia-laboratorio.
    """

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.shelf = Shelf.objects.get(pk=1)
        self.lab = Laboratory.objects.get(pk=1)
        self.lab.code = "QUG"
        self.lab.save(update_fields=["code"])
        self.unit = Catalog.objects.get(pk=63)

        self.object = Object.objects.get(pk=1)
        self.substance = Substance.objects.create(
            comercial_name="Acetona", organization=self.lab.organization
        )
        SubstanceCharacteristics.objects.filter(object_related=self.object).update(
            substance=self.substance
        )
        self.enlace = SubstanceLaboratory.objects.create(
            substance=self.substance,
            laboratory=self.lab,
            code=f"EQ-QUG-CIE-{self.substance.pk:06d}",
        )
        self.ahora = timezone.localtime()

    def crear_envase(self, obj=None):
        return ShelfObject.objects.create(
            shelf=self.shelf,
            object=obj or self.object,
            quantity=1,
            measurement_unit=self.unit,
            in_where_laboratory=self.lab,
        )

    def esperado(self, consecutivo):
        return (
            f"{self.enlace.code}-{self.ahora.year}-"
            f"{self.ahora.month:02d}-{consecutivo:04d}"
        )

    def test_first_container_of_the_month_is_0001(self):
        envase = self.crear_envase()
        self.assertEqual(envase.shelfobject_code, self.esperado(1))

    def test_counter_advances_within_the_month(self):
        primero = self.crear_envase()
        segundo = self.crear_envase()
        self.assertEqual(primero.shelfobject_code, self.esperado(1))
        self.assertEqual(segundo.shelfobject_code, self.esperado(2))

    def test_counter_restarts_next_month(self):
        self.crear_envase()
        contador = ShelfObjectCodeCounter.objects.get(substance_laboratory=self.enlace)
        # El mes siguiente es otra fila del contador, así que vuelve a empezar.
        siguiente = ShelfObjectCodeCounter.objects.create(
            substance_laboratory=self.enlace,
            year=contador.year + 1,
            month=contador.month,
            counter=0,
        )
        self.assertEqual(siguiente.counter, 0)
        self.assertEqual(contador.counter, 1)

    def test_counter_is_per_substance_laboratory(self):
        """Otra sustancia en el mismo laboratorio numera aparte."""
        otro_objeto = Object.objects.get(pk=2)
        otra = Substance.objects.create(
            comercial_name="Etanol", organization=self.lab.organization
        )
        SubstanceCharacteristics.objects.filter(object_related=otro_objeto).update(
            substance=otra
        )
        SubstanceLaboratory.objects.create(
            substance=otra, laboratory=self.lab, code=f"EQ-QUG-CIE-{otra.pk:06d}"
        )

        self.crear_envase()
        segundo = self.crear_envase(obj=otro_objeto)

        self.assertTrue(segundo.shelfobject_code.endswith("-0001"), segundo.shelfobject_code)

    def test_a_handwritten_code_is_respected(self):
        envase = ShelfObject.objects.create(
            shelf=self.shelf,
            object=self.object,
            quantity=1,
            measurement_unit=self.unit,
            in_where_laboratory=self.lab,
            shelfobject_code="MI-CODIGO",
        )
        self.assertEqual(envase.shelfobject_code, "MI-CODIGO")
        self.assertFalse(ShelfObjectCodeCounter.objects.exists())

    def test_object_without_sga_substance_gets_no_code(self):
        """Un objeto puede no venir del catálogo SGA, y eso no es un error."""
        suelto = Object.objects.create(
            name="Sin sustancia", organization=self.lab.organization, type=Object.REACTIVE
        )
        envase = self.crear_envase(obj=suelto)
        self.assertIsNone(envase.shelfobject_code)

    def test_laboratory_that_did_not_request_it_gets_no_code(self):
        otro_lab = Laboratory.objects.create(
            name="Física", organization=self.lab.organization, code="FIS"
        )
        envase = ShelfObject.objects.create(
            shelf=self.shelf,
            object=self.object,
            quantity=1,
            measurement_unit=self.unit,
            in_where_laboratory=otro_lab,
        )
        self.assertIsNone(envase.shelfobject_code)

    def test_a_failure_reserving_the_counter_does_not_break_creation(self):
        with mock.patch(
            "laboratory.shelfobject_codes.next_counter", side_effect=RuntimeError("boom")
        ):
            envase = self.crear_envase()
        self.assertIsNone(envase.shelfobject_code)
