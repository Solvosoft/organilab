"""Matriz de compatibilidad SGA (`compatibility_utils`) y los casos borde del mapa
de peligros (`hazard_map_utils`) que el escenario de equivalencia no toca.

Las consultas por objeto (N+1) de `get_zone_substances` y
`build_hcode_substance_map` se dejan como están: aquí solo se fija el
comportamiento.
"""
import os
import shutil
import tempfile

import ezodf

from laboratory.models import Catalog, Laboratory, Object, Shelf, ShelfObject
from laboratory.tests.utils import BaseLaboratorySetUpTest
from django.test import SimpleTestCase
from risk_management.compatibility_utils import (
    build_compatibility_matrix,
    build_hcode_substance_map,
    collect_h_codes,
    generate_compatibility_ods,
    get_compatibility,
    get_compatibility_reason,
    get_h_code_compatibility,
    get_incompatibility_alerts,
    get_zone_substances,
)
from risk_management.hazard_map_utils import (
    _collect_alerts,
    collect_room_shelf_hcodes,
    compute_shelf_danger,
)
from risk_management.models import Buildings, RiskZone, ZoneType
from risk_management.tests.base import indicacion
from sga.models import SubstanceCharacteristics


class CompatibilidadEntreClasesTest(SimpleTestCase):
    """Cada regla de la tabla de compatibilidad, con su motivo."""

    CASOS = [
        # (clase_a, clase_b, código, motivo)
        ("explosivos", "toxicidad_aguda", "R", "Explosivos son incompatibles"),
        ("toxicidad_aguda", "explosivos_insensibilizados", "R", "Explosivos insensibilizados"),
        ("autorreactivas", "gases_presion", "R", "autorreactivas"),
        ("piroforicos", "gases_presion", "R", "pirofóricas"),
        ("liquidos_inflamables", "gases_comburentes", "R", "Inflamables vs Comburentes"),
        ("comburentes_liq_sol", "aerosoles_inflamables", "R", "Inflamables vs Comburentes"),
        ("reactivos_agua", "liquidos_inflamables", "R", "Reactivos con agua"),
        ("gases_comburentes", "calentamiento_espontaneo", "R", "Calentamiento espontáneo"),
        ("comburentes_liq_sol", "reactivos_agua", "R", "Reactivos con agua vs Comburentes"),
        ("corrosivos_metales", "gases_comburentes", "R", "Comburentes vs Corrosivos"),
        ("toxicidad_aguda", "corrosivos_metales", "R", "Corrosivos vs Tóxicos"),
        ("corrosivos_metales", "reactivos_agua", "A", "Clases de peligro incompatibles"),
        ("liquidos_inflamables", "calentamiento_espontaneo", "A", "Clases de peligro incompatibles"),
        ("liquidos_inflamables", "gases_inflamables", "V", "Clases de peligro incompatibles"),
        ("toxicidad_aguda", "carcinogenicidad", "A", "Clases de peligro incompatibles"),
        ("gases_presion", "medio_ambiente_acuatico", "A", "Clases de peligro incompatibles"),
        ("gases_presion", "corrosivos_metales", "A", "Clases de peligro incompatibles"),
    ]

    def test_reglas(self):
        for clase_a, clase_b, codigo, motivo in self.CASOS:
            with self.subTest(a=clase_a, b=clase_b):
                self.assertEqual(get_compatibility(clase_a, clase_b), codigo)
                self.assertIn(motivo, get_compatibility_reason(clase_a, clase_b))

    def test_misma_clase_es_compatible(self):
        self.assertEqual(get_compatibility("explosivos", "explosivos"), "V")

    def test_codigos_h(self):
        self.assertEqual(get_h_code_compatibility("H225", "H272"), "R")
        self.assertEqual(get_h_code_compatibility("H225", "H999"), "A")

    def test_matriz(self):
        matriz = build_compatibility_matrix(["H225", "H272", "H300"])
        self.assertEqual(matriz["H225"]["H225"], "-")
        self.assertEqual(matriz["H225"]["H272"], "R")
        self.assertEqual(matriz["H300"]["H225"], "A")

    def test_codigos_unicos_ordenados(self):
        lab_a, lab_b = object(), object()
        sustancias = {
            lab_a: [("Etanol", ["H319", "H225"])],
            lab_b: [("Peróxido", ["H272", "H225"])],
        }
        self.assertEqual(collect_h_codes(sustancias), ["H225", "H272", "H319"])


class AlertasDeIncompatibilidadTest(BaseLaboratorySetUpTest):

    def test_solo_pares_rojos_con_su_descripcion(self):
        indicacion("H225")
        indicacion("H272")
        alertas = get_incompatibility_alerts(["H225", "H272", "H999"])
        self.assertEqual(len(alertas), 1)
        alerta = alertas[0]
        self.assertEqual((alerta["code_a"], alerta["code_b"]), ("H225", "H272"))
        self.assertEqual(alerta["desc_a"], "Indicación H225")
        self.assertIn("Inflamables vs Comburentes", alerta["reason"])

    def test_codigo_sin_indicacion_registrada(self):
        alertas = get_incompatibility_alerts(["H225", "H270X"])
        self.assertEqual(alertas, [])


class OdsDeCompatibilidadTest(BaseLaboratorySetUpTest):
    """El ODS lleva una hoja por zona con datos suficientes para una matriz."""

    def setUp(self):
        super().setUp()
        self.kg = Catalog.objects.get(key="units", description="Kilogramos")
        self.zone_type = ZoneType.objects.create(name="Industrial")
        self.building = Buildings.objects.create(
            name="Edificio de Ciencias", phone="", organization=self.org
        )
        # Laboratorio nuevo: el del fixture ya trae reactivos con códigos H.
        self.lab = Laboratory.objects.create(name="Lab compatibilidad", organization=self.org)
        self.building.laboratories.add(self.lab)
        self.carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.carpeta)

    def zona(self, nombre, laboratorios=()):
        zona = RiskZone.objects.create(
            name=nombre, organization=self.org, num_workers=2, zone_type=self.zone_type
        )
        zona.buildings.add(self.building)
        zona.laboratories.add(*laboratorios)
        return zona

    def reactivo(self, nombre, codigos, shelf_pk=1, tipo=Object.REACTIVE):
        obj = Object.objects.create(
            code=nombre[:10], name=nombre, type=tipo, organization=self.org
        )
        if codigos is not None:
            caracteristicas = SubstanceCharacteristics.objects.create(object_related=obj)
            caracteristicas.h_code.add(*[indicacion(c) for c in codigos])
        ShelfObject.objects.create(
            object=obj, shelf=Shelf.objects.get(pk=shelf_pk), quantity=1,
            measurement_unit=self.kg, in_where_laboratory=self.lab, created_by=self.user,
        )
        return obj

    def hojas(self, buildings=None, risk_zone_pks=None):
        contenido = generate_compatibility_ods(
            buildings or Buildings.objects.filter(pk=self.building.pk),
            risk_zone_pks=risk_zone_pks,
        )
        ruta = os.path.join(self.carpeta, "compatibilidad.ods")
        with open(ruta, "wb") as fh:
            fh.write(contenido.getvalue())
        doc = ezodf.opendoc(ruta)
        return {sheet.name: sheet for sheet in doc.sheets}

    def textos(self, hoja):
        return [
            hoja[fila, 0].value for fila in range(hoja.nrows()) if hoja[fila, 0].value
        ]

    def test_zona_con_incompatibilidades(self):
        self.reactivo("Etanol", ["H225"])
        self.reactivo("Peróxido", ["H272"], shelf_pk=2)
        self.reactivo("Sin códigos", [])
        self.reactivo("Sin ficha", None)
        self.reactivo("Balanza", ["H225"], tipo=Object.EQUIPMENT)
        zona = self.zona("Zona roja", [self.lab])
        hojas = self.hojas()
        self.assertEqual(list(hojas), ["Edificio de Cie - Zona roja"])
        textos = self.textos(hojas["Edificio de Cie - Zona roja"])
        self.assertIn("EDIFICIO: Edificio de Ciencias (ID: %d)" % self.building.pk, textos)
        self.assertIn("Zona de Riesgo: Zona roja (Prioridad: 0)", textos)
        self.assertIn("Codigos H presentes: H225, H272", textos)
        self.assertIn("ALERTAS DE INCOMPATIBILIDAD", textos)
        self.assertTrue(any(t.startswith("[ROJO] H225") for t in textos))
        self.assertTrue(any("Etanol (H225)" in t for t in textos))
        self.assertFalse(any("Balanza" in t for t in textos))
        self.assertEqual(
            get_zone_substances(zona),
            {self.lab: [("Etanol", ["H225"]), ("Peróxido", ["H272"])]},
        )

    def test_zona_sin_rojos(self):
        self.reactivo("Metanol", ["H225"])
        self.reactivo("Acetona", ["H225", "H319"], shelf_pk=2)
        self.zona("Zona verde", [self.lab])
        textos = self.textos(self.hojas()["Edificio de Cie - Zona verde"])
        self.assertIn("No se encontraron incompatibilidades (ROJO) en esta zona.", textos)
        self.assertNotIn("ALERTAS DE INCOMPATIBILIDAD", textos)

    def test_zonas_que_se_omiten(self):
        self.reactivo("Etanol", ["H225"])
        self.zona("Sin laboratorios")
        self.zona("Un solo código", [self.lab])
        self.assertEqual(self.hojas(), {})

    def test_filtro_por_zona(self):
        self.reactivo("Etanol", ["H225"])
        self.reactivo("Peróxido", ["H272"], shelf_pk=2)
        elegida = self.zona("Elegida", [self.lab])
        self.zona("Descartada", [self.lab])
        self.assertEqual(list(self.hojas(risk_zone_pks=[elegida.pk])), ["Edificio de Cie - Elegida"])

    def test_mapa_de_codigos_a_sustancias(self):
        self.reactivo("Etanol", ["H225", "H319"])
        self.reactivo("Metanol", ["H225"], shelf_pk=2)
        self.reactivo("Sin ficha", None)
        mapa = build_hcode_substance_map(self.zona("Zona", [self.lab]))
        self.assertEqual(
            sorted(entrada["substance"] for entrada in mapa["H225"]), ["Etanol", "Metanol"]
        )
        self.assertEqual(mapa["H319"][0]["lab"], self.lab.name)
        self.assertEqual(mapa["H319"][0]["shelf"], Shelf.objects.get(pk=1).name)


class MapaDePeligrosCasosBordeTest(BaseLaboratorySetUpTest):

    def test_reactivo_con_ficha_sin_codigos_se_lista_por_nombre(self):
        shelf = Shelf.objects.get(pk=1)
        obj = Object.objects.create(
            code="SINH", name="Sin códigos", type=Object.REACTIVE, organization=self.org
        )
        SubstanceCharacteristics.objects.create(object_related=obj)
        ShelfObject.objects.create(
            object=obj, shelf=shelf, quantity=1,
            measurement_unit=Catalog.objects.get(key="units", description="Kilogramos"),
            in_where_laboratory=self.lab, created_by=self.user,
        )
        datos = collect_room_shelf_hcodes(shelf.furniture.labroom)
        self.assertIn("Sin códigos", datos[shelf.pk]["substances"])

    def estantes(self):
        def estante(nombre, codigos):
            return {
                "name": nombre, "h_codes": set(codigos), "furniture_pk": 1, "labroom_pk": 1,
            }
        return {1: estante("Uno", ["H225"]), 2: estante("Vacío", []), 3: estante("Tres", ["H272"])}

    def test_estante_vecino_sin_codigos_no_cuenta(self):
        codigo, par = compute_shelf_danger(1, {"H225"}, self.estantes())
        self.assertEqual(codigo, "R")
        self.assertIn("H225 vs H272", par)

    def test_alertas_saltan_estantes_sin_codigos(self):
        alertas = []
        _collect_alerts(self.estantes(), alertas)
        self.assertEqual([(a["shelf_a"], a["shelf_b"]) for a in alertas], [("Uno", "Tres")])
