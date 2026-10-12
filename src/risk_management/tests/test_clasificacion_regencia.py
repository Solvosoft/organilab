"""Clasificación del establecimiento según el Decreto 44741 (`utils_risk`).

Las funciones del algoritmo se prueban con DataFrames armados a mano, con el
mismo vocabulario que usan los CSV del decreto; la lectura desde la base
(`cargar_cuadro3`, `cargar_umbral_por_H`) se prueba aparte, con los datos tal
como los guardan los cargadores de sga.
"""
import datetime
import io
import os
import shutil
import tempfile

import openpyxl
import pandas as pd
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from laboratory.models import (
    BaseUnitValues,
    Catalog,
    Laboratory,
    Object,
    ObjectMaximumLimit,
    OrganizationStructure,
)
from risk_management.models import EstablishmentLogs, RiskZone
from risk_management.tests.base import RiskTestCase, indicacion
from risk_management.utils_risk import (
    COLUMNAS_CUADRO3,
    COLUMNAS_INVENTARIO,
    _cantidad_en_toneladas,
    build_establishment_xls,
    cargar_cas_h,
    cargar_cuadro3,
    cargar_sga_referencia,
    cargar_umbral_por_H,
    clasificar_establecimiento,
    contribuciones_por_sustancia,
    create_estableshment_logs_data,
    evaluar_cuadro3,
    evaluar_cuadro4_individual,
    expandir_hcodes,
    get_inventory,
    normalizar_tipo_sga,
)
from sga.models import DangerSubstance, DangerSubstanceCategory, SubstanceCharacteristics


def inventario(*filas):
    """Filas (nombre, cas, cantidad_t, h_codes, condicion_proceso)."""
    return pd.DataFrame(
        [
            {
                "nombre": nombre,
                "cas": cas,
                "cantidad_t": cantidad,
                "h_codes": h_codes,
                "condicion_proceso": condicion,
            }
            for nombre, cas, cantidad, h_codes, condicion in filas
        ],
        columns=COLUMNAS_INVENTARIO,
    )


def cuadro3(*filas):
    """Reglas del Cuadro 3: dicts con lo que difiere de una regla por CAS vacía."""
    base = {
        "cas": "",
        "nombre": "",
        "umbral_t": float("inf"),
        "tipo_match": "cas",
        "h_codes_match": "",
        "nombre_patron": "",
        "condiciones_especiales": "",
    }
    return pd.DataFrame([dict(base, **fila) for fila in filas], columns=COLUMNAS_CUADRO3)


def cuadro4(*filas):
    """Filas (h_code, categoria, umbral_t[, condicion_proceso[, notas]])."""
    datos = []
    for fila in filas:
        h_code, categoria, umbral = fila[:3]
        condicion = fila[3] if len(fila) > 3 else ""
        notas = fila[4] if len(fila) > 4 else ""
        datos.append(
            {
                "h_code": h_code,
                "categoria": categoria,
                "seccion": "",
                "condicion_proceso": condicion,
                "umbral_t": umbral,
                "notas": notas,
            }
        )
    return pd.DataFrame(datos)


SIN_CUADRO3 = cuadro3()


class EvaluarCuadro3Test(TestCase):
    """Paso 2: sustancias nominadas por CAS, por categoría H o por patrón de nombre."""

    def test_regla_por_categoria_h_aplica_el_umbral_mas_bajo(self):
        c3 = cuadro3(
            {"tipo_match": "h_categoria", "h_codes_match": "H300", "umbral_t": 5.0},
            {"tipo_match": "h_categoria", "h_codes_match": "h300; H301", "umbral_t": 2.0},
            {"tipo_match": "h_categoria", "h_codes_match": "H300", "umbral_t": 8.0},
            {"tipo_match": "h_categoria", "h_codes_match": "H999", "umbral_t": 0.1},
        )
        inv = inventario(
            ("Tóxico", "1-1-1", 1.0, "H300;H311", ""),
            ("Inocuo", "2-2-2", 1.0, "H999X", ""),
        )
        res = evaluar_cuadro3(inv, c3).set_index("nombre")
        self.assertEqual(res.loc["Tóxico", "umbral_c3"], 2.0)
        self.assertTrue(res.loc["Tóxico", "nominada_c3"])
        self.assertEqual(res.loc["Tóxico", "ratio_c3"], 0.5)
        self.assertFalse(res.loc["Inocuo", "nominada_c3"])
        self.assertTrue(pd.isna(res.loc["Inocuo", "ratio_c3"]))

    def test_regla_por_patron_de_nombre_solo_baja_el_umbral(self):
        c3 = cuadro3(
            {"cas": "143-33-9", "umbral_t": 5.0},
            {"tipo_match": "nombre_patron", "nombre_patron": "cianuro; arsénico", "umbral_t": 3.0},
            {"tipo_match": "nombre_patron", "nombre_patron": "CIANURO", "umbral_t": 10.0},
        )
        inv = inventario(
            ("Cianuro de sodio", "143-33-9", 6.0, "", ""),
            ("Trióxido de arsénico", "1327-53-3", 1.5, "", ""),
            ("Agua", "7732-18-5", 100.0, "", ""),
        )
        res = evaluar_cuadro3(inv, c3).set_index("nombre")
        self.assertEqual(res.loc["Cianuro de sodio", "umbral_c3"], 3.0)
        self.assertEqual(res.loc["Cianuro de sodio", "ratio_c3"], 2.0)
        self.assertEqual(res.loc["Trióxido de arsénico", "umbral_c3"], 3.0)
        self.assertFalse(res.loc["Agua", "nominada_c3"])

    def test_umbral_cero_no_da_ratio(self):
        inv = inventario(("Raro", "9-9-9", 1.0, "", ""))
        res = evaluar_cuadro3(inv, cuadro3({"cas": "9-9-9", "umbral_t": 0.0}))
        self.assertTrue(res.iloc[0]["nominada_c3"])
        self.assertTrue(pd.isna(res.iloc[0]["ratio_c3"]))


class ClasificarEstablecimientoTest(TestCase):

    def test_nominada_sobre_su_umbral_es_riesgo_mayor(self):
        inv = inventario(
            ("Cloro", "7782-50-5", 15.0, "H270", ""),
            ("Agua", "7732-18-5", 1.0, "", ""),
        )
        res = clasificar_establecimiento(
            inv, cuadro3({"cas": "7782-50-5", "umbral_t": 10.0}), cuadro4(), {}
        )
        self.assertEqual(res["clasificacion"], "riesgo mayor")
        self.assertIn("Cuadro 3", res["criterio"])
        self.assertEqual(res["sumatorias_por_categoria"], {})
        detalles = {d["nombre"]: d for d in res["detalles"]}
        self.assertEqual(detalles["Cloro"]["ratio_c3"], 1.5)
        self.assertEqual(detalles["Cloro"]["umbral_c3"], 10.0)
        self.assertTrue(detalles["Cloro"]["nominada_c3"])
        self.assertIsNone(detalles["Agua"]["umbral_c3"])
        self.assertIsNone(detalles["Agua"]["ratio_c3"])

    def test_umbral_individual_del_cuadro4_es_riesgo_mayor(self):
        inv = inventario(
            ("Etanol", "64-17-5", 12.0, "H225", ""),
            ("Hexano", "110-54-3", 1.0, "H225", ""),
        )
        res = clasificar_establecimiento(
            inv,
            cuadro3({"cas": "110-54-3", "umbral_t": 50.0}),
            cuadro4(("H225", "Físico", 10.0)),
            {},
        )
        self.assertEqual(res["clasificacion"], "riesgo mayor")
        self.assertIn("Etanol", res["criterio"])
        self.assertIn("H225", res["criterio"])
        detalles = {d["nombre"]: d for d in res["detalles"]}
        self.assertTrue(detalles["Etanol"]["paso4_supera"])
        self.assertFalse(detalles["Hexano"]["paso4_supera"])
        self.assertEqual(detalles["Hexano"]["umbral_c3"], 50.0)
        self.assertEqual(detalles["Hexano"]["ratio_c3"], 0.02)
        self.assertIsNone(detalles["Etanol"]["ratio_c3"])

    def test_sumatoria_por_categoria_igual_o_mayor_a_uno_es_riesgo_mayor(self):
        inv = inventario(
            ("Etanol", "64-17-5", 30.0, "H225", ""),
            ("Acetona", "67-64-1", 25.0, "H225", ""),
        )
        res = clasificar_establecimiento(
            inv, SIN_CUADRO3, cuadro4(("H225", "Físico", 50.0)), {"H225": "Físico"}
        )
        self.assertEqual(res["clasificacion"], "riesgo mayor")
        self.assertIn("≥ 1", res["criterio"])
        self.assertEqual(res["sumatorias_por_categoria"]["Físico"], 1.1)
        # Regla de inclusión de Salud: toda sustancia del Cuadro 4 suma a Salud.
        self.assertEqual(res["sumatorias_por_categoria"]["Salud"], 1.1)
        self.assertEqual(res["sumatorias_por_categoria"]["Ambiental"], 0.0)
        self.assertTrue(res["detalles"][0]["regla_cruzada_salud"])
        self.assertEqual(res["advertencias"], [])

    def test_sumatoria_menor_a_uno_es_riesgo_menor(self):
        inv = inventario(
            ("Etanol", "64-17-5", 1.0, "H225", ""),
            ("Vertido", "1-1-1", 1.0, "H400", ""),
            ("Sin códigos", "2-2-2", 1.0, "", ""),
        )
        res = clasificar_establecimiento(
            inv,
            SIN_CUADRO3,
            cuadro4(("H225", "Físico", 50.0), ("H400", "Ambiental", 100.0), ("H400", "Salud", 200.0)),
            {},
        )
        self.assertEqual(res["clasificacion"], "riesgo menor")
        self.assertIn("< 1", res["criterio"])
        self.assertEqual(
            res["sumatorias_por_categoria"],
            {"Físico": 0.02, "Salud": 0.025, "Ambiental": 0.01},
        )
        detalles = {d["nombre"]: d for d in res["detalles"]}
        self.assertEqual(detalles["Sin códigos"]["contribuciones"], {})
        self.assertFalse(detalles["Vertido"]["regla_cruzada_salud"])

    def test_categoria_fuera_de_las_tres_conocidas_no_suma(self):
        inv = inventario(("Raro", "1-1-1", 10.0, "H225", ""))
        res = clasificar_establecimiento(
            inv, SIN_CUADRO3, cuadro4(("H225", "Otra", 50.0)), {}
        )
        self.assertEqual(res["sumatorias_por_categoria"]["Físico"], 0.0)
        self.assertEqual(res["sumatorias_por_categoria"]["Salud"], 0.2)

    def test_advertencias_llevan_el_nombre_de_la_sustancia(self):
        inv = inventario(("Etanol", "64-17-5", 1.0, "H225", ""))
        c4 = cuadro4(
            ("H225", "Físico", 50.0, "Almacenamiento"), ("H225", "Físico", 10.0, "Proceso")
        )
        res = clasificar_establecimiento(inv, SIN_CUADRO3, c4, {})
        self.assertEqual(len(res["advertencias"]), 1)
        self.assertTrue(res["advertencias"][0].startswith("Etanol: H225"))


class CondicionesDeProcesoTest(TestCase):
    """Cuando un código H tiene umbrales por condición de proceso se usa el de la
    condición de la sustancia y, si no la hay o no coincide, el más bajo (con
    advertencia en la sumatoria)."""

    C4 = cuadro4(
        ("H225", "Físico", 50.0, "Almacenamiento"),
        ("H225", "Físico", 10.0, "Proceso"),
    )

    def fila(self, cantidad, condicion):
        return inventario(("Etanol", "64-17-5", cantidad, "H225", condicion)).iloc[0]

    def test_condicion_que_coincide(self):
        res = contribuciones_por_sustancia(self.fila(5.0, "Almacenamiento"), self.C4, {})
        self.assertEqual(res["contribuciones"]["Físico"], 0.1)
        self.assertEqual(res["advertencias"], [])
        self.assertFalse(evaluar_cuadro4_individual(self.fila(20.0, "Almacenamiento"), self.C4)["supera"])

    def test_condicion_que_no_coincide_usa_el_umbral_mas_bajo(self):
        res = contribuciones_por_sustancia(self.fila(5.0, "Otra"), self.C4, {})
        self.assertEqual(res["contribuciones"]["Físico"], 0.5)
        self.assertIn("no coincide", res["advertencias"][0])
        individual = evaluar_cuadro4_individual(self.fila(20.0, "Otra"), self.C4)
        self.assertTrue(individual["supera"])
        self.assertEqual(individual["umbral"], 10.0)
        self.assertEqual(individual["categoria"], "Físico")

    def test_sin_condicion_usa_el_umbral_mas_bajo(self):
        res = contribuciones_por_sustancia(self.fila(5.0, ""), self.C4, {})
        self.assertEqual(res["contribuciones"]["Físico"], 0.5)
        self.assertIn("no especificada", res["advertencias"][0])
        self.assertTrue(evaluar_cuadro4_individual(self.fila(20.0, ""), self.C4)["supera"])


class ContribucionesPorSustanciaTest(TestCase):

    def fila(self, cantidad=5.0, h_codes="H225"):
        return inventario(("Etanol", "64-17-5", cantidad, h_codes, "")).iloc[0]

    def test_sin_codigos_sin_cantidad_o_sin_coincidencias_no_contribuye(self):
        c4 = cuadro4(("H225", "Físico", 10.0))
        for fila in (self.fila(h_codes=""), self.fila(cantidad=0), self.fila(h_codes="H999")):
            with self.subTest(fila=dict(fila)):
                res = contribuciones_por_sustancia(fila, c4, {})
                self.assertEqual(res["contribuciones"], {})
                self.assertFalse(evaluar_cuadro4_individual(fila, c4)["supera"])

    def test_umbral_cero_no_contribuye(self):
        res = contribuciones_por_sustancia(self.fila(), cuadro4(("H225", "Físico", 0.0)), {})
        self.assertEqual(res["contribuciones"], {})
        self.assertFalse(evaluar_cuadro4_individual(self.fila(), cuadro4(("H225", "Físico", 0.0)))["supera"])

    def test_las_notas_del_cuadro4_van_al_detalle(self):
        res = contribuciones_por_sustancia(
            self.fila(), cuadro4(("H225", "Físico", 10.0, "", "Nota del decreto")), {}
        )
        self.assertIn("[Nota del decreto]", res["detalle"][0])
        sin_nota = contribuciones_por_sustancia(self.fila(), cuadro4(("H225", "Físico", 10.0)), {})
        self.assertNotIn("[", sin_nota["detalle"][0])

    def test_regla_cruzada_de_salud_cita_los_codigos_sga_de_salud(self):
        c4 = cuadro4(("H225", "Físico", 10.0))
        con = contribuciones_por_sustancia(self.fila(), c4, {"H225": "Salud"})
        self.assertTrue(con["regla_cruzada_salud"])
        self.assertEqual(con["contribuciones"]["Salud"], 0.5)
        self.assertIn("H225", con["detalle"][-1])
        sin = contribuciones_por_sustancia(self.fila(), c4, {})
        self.assertIn("ninguno", sin["detalle"][-1])

    def test_con_contribucion_directa_de_salud_no_aplica_la_regla_cruzada(self):
        res = contribuciones_por_sustancia(self.fila(), cuadro4(("H225", "Salud", 10.0)), {})
        self.assertFalse(res["regla_cruzada_salud"])
        self.assertEqual(res["contribuciones"], {"Salud": 0.5})


class UtilidadesTest(TestCase):

    def test_expandir_hcodes(self):
        self.assertEqual(expandir_hcodes(""), [])
        self.assertEqual(expandir_hcodes(None), [])
        self.assertEqual(expandir_hcodes(" h225; ;H300 "), ["H225", "H300"])

    def test_normalizar_tipo_sga(self):
        self.assertEqual(normalizar_tipo_sga(" Peligros físicos "), "Físico")
        self.assertEqual(normalizar_tipo_sga("PELIGROS PARA LA SALUD"), "Salud")
        self.assertEqual(normalizar_tipo_sga(" Otro "), "Otro")

    def test_cargar_cas_h(self):
        carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, carpeta)
        ruta = os.path.join(carpeta, "cas_h.csv")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write("cas,h_codes\n 64-17-5 , H225;H319 \n7732-18-5,\n")
        self.assertEqual(
            cargar_cas_h(ruta), {"64-17-5": "H225;H319", "7732-18-5": ""}
        )
        incompleto = os.path.join(carpeta, "incompleto.csv")
        with open(incompleto, "w", encoding="utf-8") as fh:
            fh.write("cas\n64-17-5\n")
        with self.assertRaises(ValueError):
            cargar_cas_h(incompleto)

    def test_cargar_sga_referencia(self):
        indicacion("H225", danger_type="Físico")
        indicacion("h999x", danger_type="Salud")
        mapa = cargar_sga_referencia()
        self.assertEqual(mapa["H225"], "Físico")
        self.assertEqual(mapa["H999X"], "Salud")


class LecturaDesdeLaBaseTest(TestCase):
    """`cargar_cuadro3` y `cargar_umbral_por_H` con los datos tal como los guardan
    `load_danger_substances` y `load_danger_substances_category`.

    Los cargadores traducen el vocabulario de los CSV al del modelo («h_categoria»
    → «type_match», «Físico» → «physical», la condición → Catalog) y la lectura no
    lo deshacía: ninguna regla por categoría H ni por patrón se aplicaba, Físico y
    Ambiental nunca sumaban y ninguna condición de proceso coincidía.
    """

    def setUp(self):
        self.h225 = indicacion("H225")
        self.h300 = indicacion("H300")
        self.almacenamiento = Catalog.objects.create(
            key="process_condition", description="Almacenamiento"
        )

    def test_cuadro3_deshace_el_vocabulario_del_modelo(self):
        por_h = DangerSubstance.objects.create(
            name="Tóxicos agudos", type_match="type_match", threshold=5
        )
        por_h.h_codes_match.add(self.h300, self.h225)
        DangerSubstance.objects.create(
            name="Cianuros", type_match="patron_name", patron_name=" cianuro ", threshold=None
        )
        DangerSubstance.objects.create(name="Acetona", cas_code=" 67-64-1 ", threshold=2)
        df = cargar_cuadro3().set_index("nombre")
        self.assertEqual(len(df), 3)
        self.assertEqual(df.loc["Tóxicos agudos", "tipo_match"], "h_categoria")
        self.assertEqual(df.loc["Tóxicos agudos", "h_codes_match"], "H225;H300")
        self.assertEqual(df.loc["Cianuros", "tipo_match"], "nombre_patron")
        self.assertEqual(df.loc["Cianuros", "nombre_patron"], "cianuro")
        self.assertEqual(df.loc["Cianuros", "umbral_t"], float("inf"))
        self.assertEqual(df.loc["Acetona", "tipo_match"], "cas")
        self.assertEqual(df.loc["Acetona", "cas"], "67-64-1")

    def test_regla_por_categoria_h_guardada_en_la_base_nomina_la_sustancia(self):
        regla = DangerSubstance.objects.create(
            name="Tóxicos agudos", type_match="type_match", threshold=5
        )
        regla.h_codes_match.add(self.h300)
        inv = inventario(("Plaguicida", "1-1-1", 6.0, "H300", ""))
        res = clasificar_establecimiento(inv, cargar_cuadro3(), cargar_umbral_por_H(), {})
        self.assertEqual(res["clasificacion"], "riesgo mayor")
        self.assertIn("Cuadro 3", res["criterio"])

    def test_sustancia_con_varios_codigos_no_se_duplica_en_el_inventario(self):
        regla = DangerSubstance.objects.create(
            name="Etanol", cas_code="64-17-5", type_match="cas", threshold=500
        )
        regla.h_codes_match.add(self.h225, self.h300)
        inv = inventario(("Etanol", "64-17-5", 1.0, "H225", ""))
        res = evaluar_cuadro3(inv, cargar_cuadro3())
        self.assertEqual(len(res), 1)
        self.assertEqual(res.iloc[0]["umbral_c3"], 500)

    def test_sustancia_sin_tipo_se_compara_por_cas(self):
        DangerSubstance.objects.create(name="Acetona", cas_code="67-64-1", threshold=2)
        inv = inventario(("Acetona", "67-64-1", 3.0, "", ""))
        res = evaluar_cuadro3(inv, cargar_cuadro3())
        self.assertTrue(res.iloc[0]["nominada_c3"])

    def test_cuadro4_deshace_el_vocabulario_del_modelo(self):
        DangerSubstanceCategory.objects.create(
            h_code=self.h225, category="physical", section=" p5a ",
            process_condition=self.almacenamiento, threshold=10, note="Nota",
        )
        DangerSubstanceCategory.objects.create(h_code=self.h300, category="health", threshold=None)
        df = cargar_umbral_por_H().set_index("h_code")
        self.assertEqual(df.loc["H225", "categoria"], "Físico")
        self.assertEqual(df.loc["H225", "seccion"], "P5A")
        self.assertEqual(df.loc["H225", "condicion_proceso"], "Almacenamiento")
        self.assertEqual(df.loc["H225", "notas"], "Nota")
        self.assertEqual(df.loc["H300", "categoria"], "Salud")
        self.assertEqual(df.loc["H300", "condicion_proceso"], "")
        self.assertTrue(pd.isna(df.loc["H300", "umbral_t"]))

    def test_sumatoria_fisica_guardada_en_la_base_clasifica_como_riesgo_mayor(self):
        DangerSubstanceCategory.objects.create(h_code=self.h225, category="physical", threshold=10)
        inv = inventario(
            ("Etanol", "64-17-5", 6.0, "H225", ""),
            ("Acetona", "67-64-1", 6.0, "H225", ""),
        )
        res = clasificar_establecimiento(inv, cargar_cuadro3(), cargar_umbral_por_H(), {})
        self.assertEqual(res["sumatorias_por_categoria"]["Físico"], 1.2)
        self.assertEqual(res["clasificacion"], "riesgo mayor")

    def test_condicion_de_proceso_guardada_en_la_base_coincide(self):
        DangerSubstanceCategory.objects.create(
            h_code=self.h225, category="physical", process_condition=self.almacenamiento,
            threshold=50, section="A",
        )
        DangerSubstanceCategory.objects.create(
            h_code=self.h225, category="physical", threshold=10, section="B",
            process_condition=Catalog.objects.create(key="process_condition", description="Proceso"),
        )
        fila = inventario(("Etanol", "64-17-5", 5.0, "H225", "Almacenamiento")).iloc[0]
        res = contribuciones_por_sustancia(fila, cargar_umbral_por_H(), {})
        self.assertEqual(res["contribuciones"]["Físico"], 0.1)
        self.assertEqual(res["advertencias"], [])


class BuildEstablishmentXlsTest(TestCase):

    def resultado(self, **extra):
        res = {
            "clasificacion": "riesgo mayor",
            "criterio": "Sumatoria",
            "sumatorias_por_categoria": {"Físico": 1.2, "Salud": 0.3, "Ambiental": 0.0},
            "detalles": [
                {
                    "nombre": "Etanol",
                    "cas": "64-17-5",
                    "cantidad_t": 6.0,
                    "nominada_c3": False,
                    "umbral_c3": None,
                    "ratio_c3": None,
                    "h_codes": "H225",
                    "contribuciones": {"Físico": 0.6},
                    "detalle_contribuciones": ["uno", "dos"],
                    "regla_cruzada_salud": True,
                    "advertencias": ["cuidado"],
                }
            ],
        }
        res.update(extra)
        return res

    def libro(self, res):
        return openpyxl.load_workbook(io.BytesIO(build_establishment_xls(res)))

    def test_resumen_y_detalle(self):
        wb = self.libro(self.resultado())
        self.assertEqual(len(wb.worksheets), 2)
        resumen, detalle = wb.worksheets
        self.assertEqual(resumen["B1"].value, "riesgo mayor")
        self.assertEqual(resumen["B2"].value, "Sumatoria")
        self.assertEqual(
            [(fila[0].value, fila[1].value) for fila in resumen.iter_rows(min_row=6)],
            [("Físico", 1.2), ("Salud", 0.3), ("Ambiental", 0.0)],
        )
        self.assertEqual(detalle["A2"].value, "Etanol")
        self.assertEqual(detalle["H2"].value, 0.6)
        self.assertEqual(detalle["L2"].value, "uno\ndos")
        self.assertEqual(detalle["M2"].value, "cuidado")

    def test_advertencias_globales_en_hoja_propia(self):
        wb = self.libro(self.resultado(advertencias=["Etanol: H225 sin condición"]))
        self.assertEqual(len(wb.worksheets), 3)
        self.assertEqual(wb.worksheets[2]["A2"].value, "Etanol: H225 sin condición")


class CantidadEnToneladasTest(TestCase):

    def test_unidad_con_valor_si_cero_no_revienta(self):
        unidad = Catalog.objects.create(key="units", description="Unidad rota")
        BaseUnitValues.objects.create(
            measurement_unit=unidad, measurement_unit_base=unidad, si_value=0
        )
        limite = ObjectMaximumLimit(quantity=5, measurement_unit=unidad)
        self.assertEqual(_cantidad_en_toneladas(limite, None, None), 0)


class GetInventoryCasosBordeTest(TestCase):

    def setUp(self):
        org = OrganizationStructure.objects.create(name="Org inventario")
        self.lab = Laboratory.objects.create(name="Lab inventario", organization=org)
        self.kg = Catalog.objects.create(key="units", description="Kg inventario")
        BaseUnitValues.objects.create(
            measurement_unit=self.kg, measurement_unit_base=self.kg, si_value=1
        )
        self.obj = Object.objects.create(name="Etanol", code="ETA", type="0", organization=org)

    def test_sin_filtros_toma_todos_los_limites(self):
        ObjectMaximumLimit.objects.create(
            laboratory=self.lab, object=self.obj, quantity=3000, measurement_unit=self.kg
        )
        inv = get_inventory()
        self.assertEqual(list(inv["nombre"]), ["Etanol"])
        self.assertAlmostEqual(inv.iloc[0]["cantidad_t"], 3.0)

    def test_condicion_fuera_del_catalogo_no_suma(self):
        """Un límite con una condición que no es `process_condition` no tiene
        cantidad que sumar: el objeto no aparece."""
        otra = Catalog.objects.create(key="otra_clave", description="Otra")
        ObjectMaximumLimit.objects.create(
            laboratory=self.lab, object=self.obj, quantity=3000,
            measurement_unit=self.kg, process_condition=otra,
        )
        self.assertTrue(get_inventory().empty)

    def test_codigos_h_de_la_sustancia(self):
        caracteristicas = SubstanceCharacteristics.objects.create(object_related=self.obj)
        caracteristicas.h_code.add(indicacion("H225"), indicacion("H319"))
        ObjectMaximumLimit.objects.create(
            laboratory=self.lab, object=self.obj, quantity=1000, measurement_unit=self.kg
        )
        self.assertEqual(sorted(get_inventory().iloc[0]["h_codes"].split(";")), ["H225", "H319"])


class EstablishmentLogsTest(RiskTestCase):
    """`create_estableshment_logs_data` y la tarea diaria que la usa."""

    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)
        self.ayer = datetime.date.today() - datetime.timedelta(days=1)
        self.kg = Catalog.objects.create(key="units", description="Kg bitácora")
        BaseUnitValues.objects.create(
            measurement_unit=self.kg, measurement_unit_base=self.kg, si_value=1
        )
        self.obj = Object.objects.create(
            name="Etanol", code="ETA", type="0", organization=self.organization
        )
        caracteristicas = SubstanceCharacteristics.objects.create(object_related=self.obj)
        h225 = indicacion("H225")
        caracteristicas.h_code.add(h225)
        DangerSubstanceCategory.objects.create(h_code=h225, category="physical", threshold=10)

    def limite(self, quantity, lab=None):
        limite = ObjectMaximumLimit.objects.create(
            laboratory=lab or self.lab, object=self.obj, quantity=quantity,
            measurement_unit=self.kg,
        )
        ObjectMaximumLimit.objects.filter(pk=limite.pk).update(created_at=self.ayer)

    def logs(self, element):
        return EstablishmentLogs.objects.filter(
            content_type=ContentType.objects.get_for_model(element), object_id=element.pk
        )

    def test_con_inventario_guarda_clasificacion_y_excel(self):
        self.limite(12000)
        create_estableshment_logs_data(self.zone, self.ayer, [self.lab.pk])
        log = self.logs(self.zone).get()
        self.assertEqual(log.establishment_status, "Riesgo mayor")
        self.assertIn("riesgo mayor", log.table_content)
        self.assertTrue(log.xls_content.name.endswith(".xlsx"))
        self.assertEqual(str(log), "Riesgo mayor")

    def test_sin_inventario_queda_desconocido(self):
        create_estableshment_logs_data(self.zone, self.ayer, [self.lab.pk])
        log = self.logs(self.zone).get()
        self.assertEqual(log.establishment_status, "Desconocido")
        self.assertEqual((log.physical, log.health, log.environmental), (0.0, 0.0, 0.0))

    def test_sin_laboratorios_no_consulta_el_inventario_global(self):
        """Sin laboratorios no se filtraría por ninguno y el inventario sería el de
        todas las organizaciones: por eso no se registra nada."""
        self.limite(12000)
        create_estableshment_logs_data(self.zone, self.ayer, [])
        self.assertFalse(self.logs(self.zone).exists())

    def test_la_tarea_diaria_registra_zonas_y_organizaciones(self):
        from risk_management.tasks import create_establishment_reports

        self.limite(1000)
        self.limite(12000, lab=self.other_lab)
        zona_sin_edificios = RiskZone.objects.create(
            name="Sin edificios", organization=self.organization, num_workers=1,
            zone_type=self.zone_type,
        )
        create_establishment_reports()
        self.assertEqual(self.logs(self.zone).get().establishment_status, "Riesgo menor")
        self.assertEqual(self.logs(self.other_zone).get().establishment_status, "Riesgo mayor")
        self.assertEqual(self.logs(self.organization).get().establishment_status, "Riesgo menor")
        self.assertEqual(self.logs(self.other).get().establishment_status, "Riesgo mayor")
        self.assertFalse(self.logs(zona_sin_edificios).exists())
