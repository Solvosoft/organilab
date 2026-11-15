"""Cálculos de las cartas de control (``laboratory/equipment/spc.py``), sin base de datos.

Los datos salen del registro de la balanza LB-127 del laboratorio (punto de 5 g, cinco
lecturas por subgrupo, error de indicación de las pesas 0.0032 g).
"""
from decimal import Decimal as D

from django.test import SimpleTestCase

from laboratory.equipment import spc

LB127 = [
    ["5", "5", "5", "5", "5"],
    ["5", "4.99", "5", "5", "5"],
    ["5", "5", "4.99", "5", "5"],
    ["4.99", "5", "5.01", "5", "5"],
    ["5", "4.99", "5", "5", "5"],
    ["5.01", "5", "5", "4.99", "5"],
]
CORRECCION = D("0.0032")


class ConstantesTest(SimpleTestCase):

    def test_tabla_estandar_para_n_5(self):
        constantes = spc.default_constants(spc.XBAR_R, 5)
        self.assertEqual(constantes["a2"], D("0.577"))
        self.assertEqual(constantes["d3"], D("0"))
        # El Excel del laboratorio usa 2.225; el valor de la tabla para n = 5 es 2.114.
        self.assertEqual(constantes["d4"], D("2.114"))

    def test_i_mr(self):
        constantes = spc.default_constants(spc.I_MR, 1)
        self.assertEqual((constantes["a2"], constantes["d4"]), (D("2.660"), D("3.267")))

    def test_n_fuera_de_tabla(self):
        with self.assertRaises(ValueError):
            spc.default_constants(spc.XBAR_R, 1)


class SubgrupoTest(SimpleTestCase):

    def test_media_rango_y_corregida(self):
        media, rango, corregida = spc.subgroup_stats(["4.99", "5", "5.01", "5", "5"], CORRECCION)
        self.assertEqual(media, D("5"))
        self.assertEqual(rango, D("0.02"))
        self.assertEqual(corregida, D("4.9968"))

    def test_acepta_coma_decimal(self):
        self.assertEqual(spc.subgroup_stats(["4,99", "5,01"])[1], D("0.02"))

    def test_rangos_moviles(self):
        self.assertEqual(spc.moving_ranges(["5", "5.01", "4.99"]), [None, D("0.01"), D("0.02")])


class LimitesTest(SimpleTestCase):

    def test_x_r_del_registro_de_la_balanza(self):
        stats = [spc.subgroup_stats(valores, CORRECCION) for valores in LB127]
        limites = spc.limits(
            spc.XBAR_R, [corregida for _m, _r, corregida in stats], [rango for _m, rango, _c in stats],
            spc.default_constants(spc.XBAR_R, 5),
        )
        r_barra = sum((rango for _m, rango, _c in stats), D(0)) / 6
        x_barra = sum((corregida for _m, _r, corregida in stats), D(0)) / 6
        self.assertEqual(limites["center"], x_barra)
        self.assertEqual(limites["range_center"], r_barra)
        self.assertEqual(limites["ucl"], x_barra + D("0.577") * r_barra)
        self.assertEqual(limites["lcl"], x_barra - D("0.577") * r_barra)
        self.assertEqual(limites["range_ucl"], D("2.114") * r_barra)
        self.assertEqual(limites["range_lcl"], D("0"))
        self.assertLess(limites["center"], D("5"))  # la corrección baja la línea central

    def test_i_mr_usa_rangos_moviles(self):
        limites = spc.limits(spc.I_MR, ["5", "5.02", "5", "4.98"], [], spc.default_constants(spc.I_MR, 1))
        self.assertEqual(limites["center"], D("5"))
        self.assertEqual(limites["range_center"], D("0.02"))
        self.assertEqual(limites["ucl"], D("5") + D("2.660") * D("0.02"))
        self.assertEqual(limites["range_ucl"], D("3.267") * D("0.02"))

    def test_periodo_vacio(self):
        with self.assertRaises(ValueError):
            spc.limits(spc.XBAR_R, [], [], spc.default_constants(spc.XBAR_R, 5))
        with self.assertRaises(ValueError):
            spc.limits(spc.I_MR, ["5"], [], spc.default_constants(spc.I_MR, 1))


class EvaluacionTest(SimpleTestCase):
    LIMITES = {"center": D("5"), "ucl": D("5.01"), "lcl": D("4.99"),
               "range_center": D("0.01"), "range_ucl": D("0.02"), "range_lcl": D("0")}

    def test_dentro(self):
        self.assertEqual(spc.evaluate(D("5.005"), D("0.01"), self.LIMITES), (False, False, []))

    def test_media_fuera(self):
        self.assertEqual(spc.evaluate(D("5.02"), D("0.01"), self.LIMITES)[2], ["mean"])

    def test_rango_fuera(self):
        fuera, _aceptacion, motivos = spc.evaluate(D("5"), D("0.05"), self.LIMITES)
        self.assertTrue(fuera)
        self.assertEqual(motivos, ["range"])

    def test_criterio_de_aceptacion(self):
        fuera, aceptacion, motivos = spc.evaluate(D("5.008"), D("0.01"), self.LIMITES, nominal="5", tolerance="0.005")
        self.assertFalse(fuera)
        self.assertTrue(aceptacion)
        self.assertEqual(motivos, ["acceptance"])

    def test_sin_limites_solo_aceptacion(self):
        self.assertEqual(spc.evaluate(D("5.1"), None, None), (False, False, []))
