from django.test import TestCase

from risk_management.utils_risk import COLUMNAS_CUADRO3, cargar_cuadro3


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
