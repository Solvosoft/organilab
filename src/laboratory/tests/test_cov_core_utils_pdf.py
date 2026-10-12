import datetime
import os
import sys
import tempfile
from unittest import mock

from django.test import SimpleTestCase, TestCase
from weasyprint import HTML

from laboratory import utils_pdf
from laboratory.models import Catalog


def generar_pdf(lineas):
    """Genera un PDF real con una línea de texto por párrafo."""
    html = "".join("<p>%s</p>" % linea for linea in lineas)
    fd, ruta = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    HTML(string="<html><body>%s</body></html>" % html).write_pdf(ruta)
    return ruta


class IdiomaYEncabezadosTest(SimpleTestCase):
    """Detección de idioma, subíndices y patrones de sección."""

    def test_normaliza_subindices_unicode(self):
        self.assertEqual(utils_pdf._normalize_subscripts("C₆H₁₂O₆"), "C6H12O6")

    def test_detecta_espanol_por_seccion(self):
        self.assertEqual(utils_pdf._detect_language("SECCIÓN 1: Identificación"), "es")

    def test_detecta_espanol_por_indicadores_sin_seccion(self):
        texto = "Hoja de datos de seguridad\nFecha de revisión 01.01.2020"
        self.assertEqual(utils_pdf._detect_language(texto), "es")

    def test_detecta_ingles_por_defecto(self):
        self.assertEqual(utils_pdf._detect_language("Safety Data Sheet"), "en")

    def test_patron_de_seccion_por_idioma(self):
        self.assertEqual(utils_pdf._section_pattern(2, "es"), r"SECCI[ÓO]N\s*2")
        self.assertEqual(utils_pdf._section_pattern(2, "en"), r"Section\s*2")


class NombreYCasTest(SimpleTestCase):

    def test_nombre_producto_espanol_antes_de_seccion_2(self):
        texto = "SECCIÓN 1\nNombre del producto: · Acetona.\nSECCIÓN 2\nNombre comercial: Otro"
        self.assertEqual(utils_pdf._extract_product_name(texto, "es"), "Acetona")

    def test_nombre_producto_ingles_sin_seccion_2(self):
        texto = "Trade name: Ethanol absolute"
        self.assertEqual(utils_pdf._extract_product_name(texto, "en"), "Ethanol absolute")

    def test_nombre_producto_muy_corto_o_ausente(self):
        self.assertIsNone(utils_pdf._extract_product_name("Product name: X", "en"))
        self.assertIsNone(utils_pdf._extract_product_name("Sin datos", "es"))

    def test_cas_en_seccion_1(self):
        texto = "SECCIÓN 1\nCAS-No. 67-64-1\nSECCIÓN 2"
        self.assertEqual(utils_pdf._extract_cas_number(texto, "es"), "67-64-1")

    def test_cas_en_seccion_3_con_patron(self):
        texto = "Section 1\nSection 2\nSection 3\nCAS Number: 64-17-5\nSection 4"
        self.assertEqual(utils_pdf._extract_cas_number(texto, "en"), "64-17-5")

    def test_cas_en_seccion_3_por_formato(self):
        texto = "Section 1\nSection 2\nSection 3\nComponente 7732-18-5"
        self.assertEqual(utils_pdf._extract_cas_number(texto, "en"), "7732-18-5")

    def test_cas_sin_encabezados_estandar(self):
        texto = "Section 2\nAlgo\nCAS 50-00-0"
        self.assertEqual(utils_pdf._extract_cas_number(texto, "en"), "50-00-0")

    def test_cas_ausente(self):
        texto = "Section 2\nSection 3\nsin numero"
        self.assertIsNone(utils_pdf._extract_cas_number(texto, "en"))


class FormulaYCodigosTest(SimpleTestCase):

    def test_formula_hill(self):
        texto = "Formula CH3COCH3 C₃H₆O (Hill)"
        self.assertEqual(utils_pdf._extract_molecular_formula(texto, "en"), "C3H6O")

    def test_formula_hill_hidrato_devuelve_la_sal(self):
        texto = "CuSO4 · H2O\nFormula H2O (Hill)"
        self.assertEqual(utils_pdf._extract_molecular_formula(texto, "en"), "CuSO4")

    def test_formula_hill_agua_sin_hidrato(self):
        self.assertEqual(utils_pdf._extract_molecular_formula("H2O (Hill)", "es"), "H2O")

    def test_formula_molecular_espanol(self):
        texto = "Fórmula molecular: C2H6O\n"
        self.assertEqual(utils_pdf._extract_molecular_formula(texto, "es"), "C2H6O")

    def test_formula_estructural_ingles(self):
        texto = "Structural formula: Na Cl\n"
        self.assertEqual(utils_pdf._extract_molecular_formula(texto, "en"), "NaCl")

    def test_formula_invalida_o_ausente(self):
        self.assertIsNone(utils_pdf._extract_molecular_formula("Formula: abc\n", "en"))
        self.assertIsNone(utils_pdf._extract_molecular_formula("nada", "es"))

    def test_codigos_h_ordenados_y_unicos(self):
        texto = "H319 H225 H319 H3361"
        self.assertEqual(utils_pdf._extract_h_codes(texto), ["H225", "H319"])


class DensidadTest(SimpleTestCase):

    def test_densidad_espanol_con_coma(self):
        texto = "Densidad relativa: aprox. 0,79"
        self.assertEqual(utils_pdf._extract_density(texto, "es"), 0.79)

    def test_densidad_ingles(self):
        texto = "Density at 20 °C: 1.05"
        self.assertEqual(utils_pdf._extract_density(texto, "en"), 1.05)

    def test_densidad_ausente(self):
        self.assertIsNone(utils_pdf._extract_density("sin valor", "en"))


class BioacumulacionSevesoPrecursorTest(SimpleTestCase):

    def test_bioacumulable_negativo_explicito(self):
        texto = "La bioacumulación es improbable."
        self.assertFalse(utils_pdf._extract_bioaccumulable(texto, "es"))

    def test_bioacumulable_seccion_12_baja(self):
        texto = "12.3 Bioaccumulative potential\nlow\n12.4 Mobility"
        self.assertFalse(utils_pdf._extract_bioaccumulable(texto, "en"))

    def test_bioacumulable_seccion_12_alta(self):
        texto = "12.3 Bioaccumulative potential\nHigh potential\n12.4 Mobility"
        self.assertTrue(utils_pdf._extract_bioaccumulable(texto, "en"))

    def test_bioacumulable_sin_datos(self):
        self.assertIsNone(utils_pdf._extract_bioaccumulable("Sección 12.3\nalgo\n12.4", "es"))
        self.assertIsNone(utils_pdf._extract_bioaccumulable("texto", "es"))

    def test_seveso(self):
        self.assertFalse(utils_pdf._extract_seveso("texto sin directiva"))
        self.assertFalse(utils_pdf._extract_seveso("Seveso III: No aplicable"))
        self.assertTrue(utils_pdf._extract_seveso("Seveso III Categoría P5c umbral 5000 t"))
        self.assertFalse(utils_pdf._extract_seveso("Seveso III mencionada"))

    def test_precursor(self):
        self.assertFalse(utils_pdf._extract_precursor("texto"))
        self.assertFalse(utils_pdf._extract_precursor("Precursor: no aplicable"))
        self.assertTrue(utils_pdf._extract_precursor("Precursor sujeto a control"))
        self.assertFalse(utils_pdf._extract_precursor("Precursor mencionado"))


class FechaRevisionTest(SimpleTestCase):

    def test_parseo_de_fechas(self):
        self.assertIsNone(utils_pdf._parse_revision_date(""))
        self.assertEqual(utils_pdf._parse_revision_date("31.12.2020"), datetime.date(2020, 12, 31))
        self.assertEqual(utils_pdf._parse_revision_date("12/31/2020"), datetime.date(2020, 12, 31))
        self.assertIsNone(utils_pdf._parse_revision_date("2020/99/99"))

    def test_fecha_revision_por_idioma(self):
        self.assertEqual(
            utils_pdf._extract_revision_date("Fecha de revisión: 01.02.2021", "es"),
            datetime.date(2021, 2, 1),
        )
        self.assertEqual(
            utils_pdf._extract_revision_date("Revision Date 2021-02-01", "en"),
            datetime.date(2021, 2, 1),
        )
        self.assertIsNone(utils_pdf._extract_revision_date("sin fecha", "en"))


class ExtraerMsdsDePdfTest(SimpleTestCase):

    def test_extrae_campos_de_un_pdf_real(self):
        ruta = generar_pdf([
            "SECCIÓN 1: Identificación",
            "Nombre del producto: Acetona",
            "CAS-No. 67-64-1",
            "Fórmula molecular: C3H6O",
            "SECCIÓN 2: Peligros H225 H319",
            "Densidad: 0,79",
            "Fecha de revisión: 01.02.2021",
        ])
        try:
            datos = utils_pdf.extract_msds_data(ruta)
        finally:
            os.remove(ruta)
        self.assertEqual(datos["_lang"], "es")
        self.assertEqual(datos["product_name"], "Acetona")
        self.assertEqual(datos["cas_id_number"], "67-64-1")
        self.assertEqual(datos["molecular_formula"], "C3H6O")
        self.assertEqual(datos["h_codes"], ["H225", "H319"])
        self.assertEqual(datos["density"], 0.79)
        self.assertEqual(datos["revision_date"], datetime.date(2021, 2, 1))
        self.assertFalse(datos["seveso_list"])
        self.assertFalse(datos["is_precursor"])

    def test_pdf_sin_texto_devuelve_none(self):
        ruta = generar_pdf([])
        try:
            self.assertIsNone(utils_pdf.extract_msds_data(ruta))
        finally:
            os.remove(ruta)

    def test_archivo_ilegible_devuelve_none(self):
        self.assertIsNone(utils_pdf.extract_msds_data("/no/existe/ficha.pdf"))

    def test_sin_pdfplumber_devuelve_none(self):
        with mock.patch.dict(sys.modules, {"pdfplumber": None}):
            self.assertIsNone(utils_pdf.extract_msds_data("ficha.pdf"))

    def test_lectura_que_excede_el_tiempo_devuelve_none(self):
        hilo = mock.MagicMock()
        hilo.is_alive.return_value = True
        with mock.patch.object(utils_pdf.threading, "Thread", return_value=hilo):
            self.assertIsNone(utils_pdf.extract_msds_data("ficha.pdf"))
        hilo.join.assert_called_once_with(timeout=utils_pdf.PDF_EXTRACT_TIMEOUT)


class CamposDeCatalogoTest(SimpleTestCase):

    def test_iarc(self):
        entradas = [(1, "Grupo 1"), (2, "Grupo 2B"), (3, "Sin grupo")]
        self.assertIsNone(utils_pdf._extract_iarc("IARC Group 1", [(3, "x")]))
        self.assertIsNone(utils_pdf._extract_iarc("sin agencia", entradas))
        self.assertEqual(utils_pdf._extract_iarc("IARC: Group 2b", entradas), 2)
        self.assertIsNone(utils_pdf._extract_iarc("IARC: no clasificado", entradas))

    def test_imdg(self):
        entradas = [(10, "Clase 1"), (11, "Clase 2"), (12, "Clase 3")]
        self.assertEqual(utils_pdf._extract_imdg("14.3 Clase 3", entradas, "es"), 12)
        self.assertEqual(utils_pdf._extract_imdg("14.3 Transport hazard class 2", entradas, "en"), 11)
        self.assertIsNone(utils_pdf._extract_imdg("sin transporte", entradas, "es"))

    def test_organos_blanco(self):
        entradas = [(1, "Hígado"), (2, "Riñón"), (3, "Bazo")]
        texto = "SECCIÓN 11\nDaña el hígado y el kidney\nSECCIÓN 12"
        self.assertEqual(utils_pdf._extract_white_organ(texto, entradas, "es"), [1, 2])
        self.assertEqual(utils_pdf._extract_white_organ("spleen", entradas, "en"), [3])

    def test_codigos_ue(self):
        entradas = [(5, "EUH066 Exposición"), (6, "EUH 019"), (7, "otra")]
        self.assertEqual(utils_pdf._extract_ue_code("EUH066", [(7, "otra")]), [])
        self.assertEqual(utils_pdf._extract_ue_code("EUH066 y EUH 019 y EUH999", entradas), [5, 6])

    def test_nfpa_por_punto_de_inflamacion(self):
        entradas = [
            (1, "Líquido clase IA"), (2, "Líquido clase IB"), (3, "Líquido clase IC"),
            (4, "Líquido clase II"), (5, "Líquido clase IIIA"),
        ]
        casos = [
            ("Flash point: -20 °C\nBoiling point: 30 °C", "en", [1]),
            ("Punto de inflamación: -20 °C", "es", [2]),
            ("Punto de inflamación: 30 °C\nPunto de ebullición: 80 °C", "es", [3]),
            ("Flash point: 40 °C", "en", [4]),
            ("Flash point: 70,5 °C", "en", [5]),
            ("Flash point: 120 °C", "en", []),
        ]
        for texto, idioma, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(utils_pdf._extract_nfpa(texto, entradas, idioma), esperado)
        self.assertEqual(utils_pdf._extract_nfpa("Flash point: 1 °C", [(9, "x")]), [])
        self.assertEqual(utils_pdf._extract_nfpa("sin datos", entradas, "en"), [])

    def test_nfpa_clase_ic_con_el_catalogo_real(self):
        """La descripción del catálogo es «Líquido inflamable clase IC»: antes el patrón
        solo admitía A/B, la clave quedaba como «I» y un punto de inflamación entre
        22,8 y 37,8 °C nunca se clasificaba."""
        entradas = [(115, "Líquido inflamable clase IB"), (116, "Líquido inflamable clase IC")]
        self.assertEqual(utils_pdf._extract_nfpa("Flash point: 30 °C", entradas, "en"), [116])

    def test_clase_de_almacenamiento(self):
        entradas = [(1, "3 Líquidos inflamables"), (2, "4.1A Sólidos"), (3, "4.1B Sólidos"), (4, "Otro")]
        self.assertEqual(utils_pdf._extract_storage_class("x", [(4, "Otro")]), [])
        self.assertEqual(utils_pdf._extract_storage_class("sin clase", entradas, "es"), [])
        self.assertEqual(utils_pdf._extract_storage_class("Clase de almacenamiento 3", entradas, "es"), [1])
        self.assertEqual(utils_pdf._extract_storage_class("Storage class 4.1 B", entradas, "en"), [3])
        entradas_numericas = [(1, "10 Líquidos"), (2, "10A Otros"), (3, "11 Sólidos")]
        self.assertEqual(utils_pdf._extract_storage_class("Storage class 10", [(2, "10A Otros"), (3, "10B")], "en"), [2, 3])
        self.assertEqual(utils_pdf._extract_storage_class("Storage class 4.1", entradas_numericas, "en"), [])

    def test_tipo_de_precursor(self):
        entradas = [(1, "Lista 1"), (2, "Lista 2"), (3, "Otro")]
        self.assertIsNone(utils_pdf._extract_precursor_type("Precursor lista 1", [(3, "Otro")]))
        self.assertIsNone(utils_pdf._extract_precursor_type("sin control", entradas))
        self.assertEqual(utils_pdf._extract_precursor_type("Precursor incluido en la Lista 2", entradas), 2)
        self.assertIsNone(utils_pdf._extract_precursor_type("Precursor sin lista", entradas))

    def test_extract_catalog_fields_combina_todo(self):
        catalogos = {"IARC": [(1, "Grupo 1")], "Precursor": [(2, "Lista 1")]}
        resultado = utils_pdf.extract_catalog_fields("IARC Group 1\nPrecursor Lista 1", catalogos)
        self.assertEqual(resultado["iarc"], 1)
        self.assertEqual(resultado["precursor_type"], 2)
        self.assertEqual(resultado["white_organ"], [])
        self.assertIsNone(resultado["imdg"])


class ConstruirCatalogoTest(TestCase):

    def test_build_catalog_dict_agrupa_por_clave(self):
        iarc = Catalog.objects.create(key="IARC", description="Grupo 1 prueba")
        Catalog.objects.create(key="otra", description="no incluida")
        catalogos = utils_pdf.build_catalog_dict()
        self.assertEqual(set(catalogos), set(utils_pdf.CATALOG_KEYS))
        self.assertIn((iarc.pk, "Grupo 1 prueba"), catalogos["IARC"])
        self.assertFalse(any(desc == "no incluida" for valores in catalogos.values() for _, desc in valores))
