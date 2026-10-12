from django.test import TestCase

from risk_management.utils_risk import (
    COLUMNAS_CUADRO3,
    COLUMNAS_INVENTARIO,
    cargar_cuadro3,
    get_inventory,
)


class CargarCuadro3Test(TestCase):
    """`cargar_cuadro3()` con la tabla de sustancias peligrosas vacía.

    Es un caso normal —una organización que aún no ha cargado su catálogo— y
    reventaba el reporte de regencia con un 500. El mensaje además culpaba a un
    `cuadro3.csv` que la función ya no lee: los datos salen de
    `DangerSubstance` desde que se migraron a la base.
    """

    def test_sin_sustancias_devuelve_marco_vacio_con_columnas(self):
        df = cargar_cuadro3()
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), list(COLUMNAS_CUADRO3))

    def test_con_sustancias_devuelve_las_columnas_esperadas(self):
        from sga.models import DangerSubstance

        DangerSubstance.objects.create(
            name="Acetona", cas_code="67-64-1", threshold=1
        )
        df = cargar_cuadro3()
        self.assertEqual(len(df), 1)
        self.assertEqual(list(df.columns), list(COLUMNAS_CUADRO3))
        self.assertEqual(df.iloc[0]["cas"], "67-64-1")


class CargarUmbralPorHTest(TestCase):
    """`cargar_umbral_por_H()` con el catálogo de categorías vacío.

    Mismo fallo que en `cargar_cuadro3`, en la función de al lado: el reporte
    de regencia reventaba en cuanto no había filas, culpando a un
    `cuadro4_h_umbral.csv` que tampoco se lee ya.
    """

    def test_sin_categorias_devuelve_marco_vacio_con_columnas(self):
        from risk_management.utils_risk import COLUMNAS_UMBRAL_H, cargar_umbral_por_H

        df = cargar_umbral_por_H()
        self.assertTrue(df.empty)
        for col in COLUMNAS_UMBRAL_H:
            self.assertIn(col, df.columns)


class GetInventoryTest(TestCase):
    """`get_inventory()`, la base del reporte de regencia.

    Reventaba el reporte en tres puntos: buscaba la unidad «Toneladas» con
    `.get()` (no existe en una base vaciada o cargada solo desde fixtures, como
    la de Selenium), devolvía un DataFrame sin columnas cuando no había límites
    (y el `drop_duplicates` posterior tiraba KeyError) y, con un límite en
    toneladas y condición de proceso, sumaba `objs_max.quantity` (atributo de
    un QuerySet, AttributeError).
    """

    def setUp(self):
        from laboratory.models import (
            BaseUnitValues,
            Catalog,
            Laboratory,
            Object,
            OrganizationStructure,
        )

        self.kg = Catalog.objects.create(key="units", description="Kg prueba")
        BaseUnitValues.objects.create(
            measurement_unit=self.kg, measurement_unit_base=self.kg, si_value=1
        )
        self.tons = Catalog.objects.filter(
            key="units", description="Toneladas"
        ).first() or Catalog.objects.create(key="units", description="Toneladas")
        self.process = Catalog.objects.create(
            key="process_condition", description="Condición prueba"
        )
        org = OrganizationStructure.objects.create(name="Org prueba")
        self.lab = Laboratory.objects.create(name="Lab A", organization=org)
        self.other_lab = Laboratory.objects.create(name="Lab B", organization=org)
        self.obj = Object.objects.create(
            name="Acetona", code="ACE", type="0", organization=org
        )

    def filters(self, lab=None):
        return {
            "object__type": 0,
            "object__isnull": False,
            "measurement_unit__isnull": False,
            "laboratory__pk__in": [(lab or self.lab).pk],
        }

    def limit(self, **kwargs):
        from laboratory.models import ObjectMaximumLimit

        data = {"laboratory": self.lab, "object": self.obj, "quantity": 2000,
                "measurement_unit": self.kg}
        data.update(kwargs)
        return ObjectMaximumLimit.objects.create(**data)

    def test_sin_unidad_toneladas_no_revienta(self):
        from laboratory.models import Catalog, ObjectMaximumLimit

        self.limit()
        ObjectMaximumLimit.objects.filter(measurement_unit=self.tons).delete()
        Catalog.objects.filter(description="Toneladas").delete()
        inv = get_inventory(self.filters())
        self.assertEqual(len(inv), 1)
        self.assertAlmostEqual(inv.iloc[0]["cantidad_t"], 2.0)

    def test_sin_limites_devuelve_marco_vacio_con_columnas(self):
        inv = get_inventory(self.filters())
        self.assertTrue(inv.empty)
        self.assertEqual(list(inv.columns), list(COLUMNAS_INVENTARIO))
        # Lo que hace el reporte de regencia justo después.
        inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])

    def test_toneladas_con_condicion_de_proceso(self):
        self.limit(measurement_unit=self.tons, quantity=3,
                   process_condition=self.process)
        inv = get_inventory(self.filters())
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv.iloc[0]["cantidad_t"], 3)
        self.assertEqual(inv.iloc[0]["condicion_proceso"], "Condición prueba")

    def test_respeta_el_filtro_de_laboratorio(self):
        """Los límites de otro laboratorio no se cuelan en el inventario."""
        self.limit(quantity=1000)
        self.limit(laboratory=self.other_lab, quantity=9000)
        inv = get_inventory(self.filters())
        self.assertAlmostEqual(inv.iloc[0]["cantidad_t"], 1.0)
