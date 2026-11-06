# -*- coding: utf-8 -*-
"""Pruebas de las piezas internas del motor de etiquetas (``sga/label_engine``).

Recursos, lienzos, medición, planificación, renderers y PDF: cada rama de
degradación (logo ausente, fuente ausente, pictograma sin archivo, frases que no
caben) debe producir una etiqueta utilizable en vez de romper.
"""
import os
import tempfile
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase
from PIL import Image, ImageFont

from sga.label_engine import LabelBlueprint, LabelEngine, LabelTooSmallError, config
from sga.label_engine import phrases_catalog
from sga.label_engine import engine as engine_mod
from sga.label_engine import utils as engine_utils
from sga.label_engine.layout.box import Box
from sga.label_engine.layout.canvas import PILCanvas, SVGCanvas
from sga.label_engine.layout.measurer import Measurer
from sga.label_engine.layout import planner as planner_mod
from sga.label_engine.layout.planner import LabelPlanner
from sga.label_engine.pdf import generate_pdf, labels_to_pdf
from sga.label_engine.renderers.accent import AccentRenderer
from sga.label_engine.renderers.logos import LogoRenderer
from sga.label_engine.renderers.phrases import HPPhrasesRenderer
from sga.label_engine.renderers.pictogram import PictogramRenderer
from sga.label_engine.renderers.text import ChemicalNameRenderer, FormulaRenderer
from sga.label_engine.resources import ResourceCache

EPP_SIMBOLO = "iso 7010 m009"


def _blueprint(ancho=70, alto=40, dpi=300, **over):
    data = {
        "nombre": "Ácido Sulfúrico",
        "simbolos": ["Corrosivo"],
        "palabra_advertencia": "PELIGRO",
        "frases_peligro": "H314",
        "consejos_prudencia": "P280",
    }
    data.update(over)
    bp = LabelBlueprint.from_dict(data)
    bp.ancho_mm, bp.alto_mm, bp.dpi = ancho, alto, dpi
    return bp


def _plan(bp, planner=None):
    planner = planner or LabelPlanner()
    ancho = int(bp.ancho_mm * bp.dpi / 25.4)
    alto = int(bp.alto_mm * bp.dpi / 25.4)
    return planner.plan(bp, ancho, alto)


def _cajas(layout, tipo):
    return [b for b in layout.boxes if b.element_type == tipo]


def _textos(layout):
    return [ln for b in _cajas(layout, "text") for ln in b.content_ref["lines"]]


class UtilsTest(SimpleTestCase):
    def test_normalize_text_no_cadena_devuelve_vacio(self):
        self.assertEqual(engine_utils.normalize_text(None), "")
        self.assertEqual(engine_utils.normalize_text(15), "")

    def test_normalize_text_conserva_texto_si_falla_la_normalizacion(self):
        with mock.patch.object(engine_utils.unicodedata, "normalize", side_effect=ValueError):
            self.assertEqual(engine_utils.normalize_text("Ácido"), "Ácido")

    def test_read_text_file_detecta_codificacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            utf8 = os.path.join(tmp, "utf8.txt")
            latin = os.path.join(tmp, "latin.txt")
            with open(utf8, "w", encoding="utf-8") as f:
                f.write("Ácido")
            with open(latin, "wb") as f:
                f.write("Ácido".encode("latin-1"))
            self.assertEqual(engine_utils.read_text_file(utf8), "Ácido")
            self.assertEqual(engine_utils.read_text_file(latin), "Ácido")
            # Ninguna codificación sirve: se lee como UTF-8 reemplazando errores.
            self.assertEqual(
                engine_utils.read_text_file(latin, encodings=("ascii",)), "�cido"
            )


class ConfigTest(SimpleTestCase):
    def test_cargar_pictogramas_epp_sin_carpeta(self):
        with mock.patch.object(config, "CARPETA_PICTOGRAMAS_EPP", "/no/existe/epp"):
            self.assertEqual(config.cargar_pictogramas_epp(), {})

    def test_cargar_pictogramas_epp_nombres_vacios_y_repetidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            for nombre in ("guantes.eps", "guantes.v2.eps", "_.eps", "leeme.txt"):
                open(os.path.join(tmp, nombre), "w").close()
            with mock.patch.object(config, "CARPETA_PICTOGRAMAS_EPP", tmp):
                epp = config.cargar_pictogramas_epp()
        self.assertEqual(
            epp,
            {
                "_": "_.eps",
                "guantes": "guantes.eps",
                "guantes (guantes.v2.eps)": "guantes.v2.eps",
            },
        )


class BlueprintModelTest(SimpleTestCase):
    def test_simbolos_que_no_son_lista_se_descartan(self):
        bp = LabelBlueprint.from_dict({"nombre": "Agua", "simbolos": "Corrosivo"})
        self.assertEqual(bp.simbolos, [])

    def test_validate_dimensiones_y_dpi(self):
        bp = LabelBlueprint(nombre="Agua", ancho_mm=0, alto_mm=40, dpi=0)
        self.assertEqual(
            bp.validate(),
            ["Las dimensiones de la etiqueta deben ser positivas", "DPI debe ser positivo"],
        )


class ResourceCacheTest(SimpleTestCase):
    def setUp(self):
        self.res = ResourceCache()

    def test_logo_inexistente_o_corrupto(self):
        self.assertIsNone(self.res.get_logo("/no/existe/logo.png"))
        with tempfile.NamedTemporaryFile(suffix=".png") as f:
            f.write(b"no es una imagen")
            f.flush()
            self.assertIsNone(self.res.get_logo(f.name))

    def test_preload_logos(self):
        self.assertEqual(self.res.preload_logos(), [])
        with mock.patch.object(config, "RUTA_LOGO_UNA", "/no/existe.png"):
            self.assertEqual(ResourceCache().preload_logos(), ["No se pudo cargar logo: una"])

    def test_fuente_por_defecto_si_no_hay_candidatas(self):
        with mock.patch.object(config, "FONT_CANDIDATES", ["/no/existe/Bold.ttf", "/no/existe.ttf"]):
            font = self.res.get_font(12, bold=True)
        self.assertIsNotNone(font)
        # Queda en caché: la segunda llamada no vuelve a buscar.
        self.assertIs(self.res.get_font(12, bold=True), font)

    def test_pictograma_en_cache_y_fallback(self):
        a = self.res.get_pictogram("Corrosivo", 40)
        self.assertIs(self.res.get_pictogram("Corrosivo", 40), a)
        desconocido = self.res.get_pictogram("Desconocido", 40)
        self.assertEqual(desconocido.size, (40, 40))

    def test_pictograma_epp_desde_miniatura(self):
        img = self.res.get_pictogram(EPP_SIMBOLO, 32)
        self.assertEqual((img.size, img.mode), ((32, 32), "RGBA"))

    def test_pictograma_epp_miniatura_corrupta_usa_eps(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "thumbs"))
            filename = config.PICTOGRAMAS_EPP[EPP_SIMBOLO]
            with open(os.path.join(tmp, "thumbs", os.path.splitext(filename)[0] + ".png"), "wb") as f:
                f.write(b"basura")
            with mock.patch.object(config, "CARPETA_PICTOGRAMAS_EPP", tmp):
                # Sin EPS en la carpeta: tras fallar la miniatura no hay archivo.
                self.assertIsNone(self.res._load_pictogram_file(EPP_SIMBOLO, 32))

    def test_pictograma_miniatura_no_rgba_se_convierte(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "thumbs"))
            filename = config.PICTOGRAMAS_EPP[EPP_SIMBOLO]
            Image.new("RGB", (10, 10), "red").save(
                os.path.join(tmp, "thumbs", os.path.splitext(filename)[0] + ".png")
            )
            with mock.patch.object(config, "CARPETA_PICTOGRAMAS_EPP", tmp):
                img = self.res._load_pictogram_file(EPP_SIMBOLO, 20)
        self.assertEqual((img.size, img.mode), ((20, 20), "RGBA"))

    def test_pictograma_archivo_ausente_o_corrupto(self):
        self.assertIsNone(self.res._load_pictogram_file("Desconocido", 20))
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(config, "CARPETA_PICTOGRAMAS", tmp):
                self.assertIsNone(self.res._load_pictogram_file("Corrosivo", 20))
                with open(os.path.join(tmp, config.PICTOGRAMAS_OSHA["Corrosivo"]), "wb") as f:
                    f.write(b"no es eps")
                self.assertIsNone(self.res._load_pictogram_file("Corrosivo", 20))

    def test_pictograma_svg(self):
        svg = self.res.get_pictogram_svg(EPP_SIMBOLO)
        self.assertIn("<svg", svg)
        self.assertIs(self.res.get_pictogram_svg(EPP_SIMBOLO), svg)
        self.assertIsNone(self.res.get_pictogram_svg("Desconocido"))

    def test_pictograma_svg_ilegible_o_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(config, "CARPETA_PICTOGRAMAS", tmp):
                self.assertIsNone(ResourceCache().get_pictogram_svg("Corrosivo"))
                # Un directorio con el nombre del SVG existe pero no se puede leer.
                os.makedirs(os.path.join(tmp, "corrosion.svg"))
                self.assertIsNone(ResourceCache().get_pictogram_svg("Corrosivo"))

    def test_pictogramas_de_respaldo_por_simbolo(self):
        simbolos = list(config.PICTOGRAMAS_OSHA) + ["Otro"]
        for simbolo in simbolos:
            with self.subTest(simbolo=simbolo):
                img = self.res._generate_fallback_pictogram(simbolo, 60)
                self.assertEqual(img.size, (60, 60))
                # El rombo reglamentario siempre se dibuja (borde rojo).
                self.assertIn((200, 16, 46, 255), [c for _, c in img.getcolors(10000)])

    def test_pictograma_de_respaldo_sin_fuente(self):
        with mock.patch.object(self.res, "get_font", side_effect=OSError):
            img = self.res._generate_fallback_pictogram("Comburente", 60)
        self.assertEqual(img.size, (60, 60))


class CanvasTest(SimpleTestCase):
    def setUp(self):
        self.font = ResourceCache().get_font(20)

    def test_pil_canvas_mide_aunque_falle_textlength(self):
        canvas = PILCanvas(50, 50)
        esperado = canvas.text_width("Hola", self.font)
        with mock.patch.object(canvas.draw, "textlength", side_effect=ValueError):
            self.assertAlmostEqual(canvas.text_width("Hola", self.font), esperado, delta=2)
        self.assertIs(canvas.image, canvas.result())

    def test_pil_canvas_pega_con_mascara(self):
        canvas = PILCanvas(10, 10)
        rojo = Image.new("RGB", (4, 4), "red")
        mascara = Image.new("L", (4, 4), 255)
        canvas.paste_image(rojo, (0, 0), mascara)
        self.assertEqual(canvas.result().getpixel((1, 1)), (255, 0, 0))

    def test_svg_canvas_ramas_defensivas(self):
        canvas = SVGCanvas(50, 50)
        esperado = canvas.text_width("Hola", self.font)
        with mock.patch.object(canvas._scratch, "textlength", side_effect=ValueError):
            self.assertAlmostEqual(canvas.text_width("Hola", self.font), esperado, delta=2)
        # Fuente sin métricas: el ascenso se aproxima con el tamaño.
        canvas.text((1, 2), "x", SimpleNamespace(size=10, path=""), "#000")
        canvas.embed_svg("no es svg", (0, 0), 10, 10)
        canvas.paste_image("no es imagen", (0, 0))
        canvas.paste_image(Image.new("L", (2, 2)), (0, 0))
        svg = canvas.result()
        self.assertIn('<text x="1" y="12"', svg)
        self.assertEqual(svg.count("<image"), 1)

    def test_svg_con_fuentes_incrustadas(self):
        svg = LabelEngine().generate_svg(_blueprint(), embed_fonts=True)
        self.assertIn("@font-face", svg)
        self.assertIn("font-weight:bold", svg)
        self.assertIn("font-weight:normal", svg)

    def test_svg_font_face_sin_fuente_disponible(self):
        canvas = SVGCanvas(10, 10, embed_fonts=True)
        self.assertEqual(canvas._font_face_defs(), "")
        canvas.text((0, 0), "a", self.font, "#000")
        with mock.patch.object(SVGCanvas, "_resolve_font_path", return_value=None):
            self.assertEqual(canvas._font_face_defs(), "")
        with mock.patch.object(SVGCanvas, "_font_bytes", return_value=None):
            self.assertEqual(canvas._font_face_defs(), "")

    def test_resolve_font_path(self):
        with mock.patch.object(config, "FONT_CANDIDATES", ["/no/existe.ttf"]):
            self.assertIsNone(SVGCanvas._resolve_font_path(False))
        self.assertIn("Bold", SVGCanvas._resolve_font_path(True))

    def test_font_bytes_sin_fonttools(self):
        path = SVGCanvas._resolve_font_path(False)
        with mock.patch.dict("sys.modules", {"fontTools.subset": None}):
            with open(path, "rb") as f:
                self.assertEqual(SVGCanvas._font_bytes(path, {"a"}), f.read())
            self.assertIsNone(SVGCanvas._font_bytes("/no/existe.ttf", {"a"}))


class MeasurerTest(SimpleTestCase):
    def setUp(self):
        self.m = Measurer(dpi=300)
        self.font = self.m.font(30)

    def test_piso_y_ajuste(self):
        self.assertEqual(self.m.font_floor_px(1.2), 14)
        self.assertEqual(self.m.font_floor_px(0.1), 8)
        self.assertTrue(self.m.fits_width("a", 1000, self.font))
        self.assertFalse(self.m.fits_width("a" * 50, 10, self.font))

    def test_wrap_vacio(self):
        self.assertEqual(self.m.wrap("   ", 100, self.font), [])

    def test_wrap_corta_palabras_mas_anchas_que_la_linea(self):
        ancho = self.m.text_width("ABCDE", self.font)
        lineas = self.m.wrap("xy ABCDEFGHIJKLMNO", ancho, self.font)
        self.assertEqual(lineas[0], "xy")
        self.assertEqual("".join(lineas[1:]), "ABCDEFGHIJKLMNO")
        for linea in lineas:
            self.assertLessEqual(self.m.text_width(linea, self.font), ancho)


class RenderersTest(SimpleTestCase):
    def setUp(self):
        self.res = ResourceCache()
        self.canvas = PILCanvas(400, 200)

    def _pintado(self):
        return self.canvas.result().getbbox() is not None and self.canvas.result().convert("L").getextrema()[0] < 255

    def test_acento_sin_color_no_pinta(self):
        AccentRenderer().render(Box(0, 0, 400, 200, "accent", {}), self.canvas, self.res)
        self.assertFalse(self._pintado())

    def test_logo_ausente_no_pinta(self):
        LogoRenderer().render(Box(0, 0, 40, 20, "logo", "/no/existe.png"), self.canvas, self.res)
        self.assertFalse(self._pintado())

    def test_pictograma_sin_imagen_no_pinta(self):
        res = mock.Mock(get_pictogram=mock.Mock(return_value=None))
        PictogramRenderer().render(Box(0, 0, 40, 40, "pictogram", {"symbol": "X"}), self.canvas, res)
        self.assertFalse(self._pintado())

    def test_frases_con_referencia_fds(self):
        plan = {"font_size": 14, "line_height": 14, "gap": 4, "h_lines": [], "p_lines": [], "fds_lines": [config.FDS_REFERENCE_TEXT]}
        HPPhrasesRenderer().render(Box(0, 0, 400, 100, "phrases", plan), self.canvas, self.res)
        self.assertTrue(self._pintado())
        # El texto FDS se pinta en gris, no en el rojo de las H.
        colores = {c for _, c in self.canvas.result().getcolors(100000)}
        self.assertIn((102, 102, 102), colores)

    def test_nombre_truncado_agrega_puntos_suspensivos(self):
        d = {"lines": ["A"], "suffix": "", "truncated": True, "font_size_main": 20, "font_size_sub": 12, "line_gap": 30}
        ChemicalNameRenderer().render(Box(0, 0, 400, 100, "name", d), self.canvas, self.res)
        caja = self.canvas.result().convert("L").point(lambda p: p < 128 and 255).getbbox()
        # Hay tinta en la segunda línea (y >= 30): los puntos suspensivos.
        self.assertGreaterEqual(caja[3], 30)

    def test_parse_formula(self):
        parse = FormulaRenderer.parse_formula
        self.assertEqual(parse("H_{2}SO_4"), [("n", "H"), ("s", "2"), ("n", "SO"), ("s", "4")])
        self.assertEqual(parse("Fe^{3+}"), [("n", "Fe"), ("p", "3+")])
        self.assertEqual(parse("X_{12"), [("n", "X"), ("s", "12")])
        self.assertEqual(parse("X_"), [("n", "X")])

    def test_formula_con_sub_superindices_estado_y_concentracion(self):
        d = {
            "formula": "Fe_{2}O_3^{2-}",
            "cas": "",
            "concentracion": "98 %",
            "estado_suffix": "(s)",
            "font_size_main": 20,
            "font_size_sub": 12,
            "font_size_sup": 12,
        }
        FormulaRenderer().render(Box(0, 0, 400, 100, "formula", d), self.canvas, self.res)
        caja = self.canvas.result().convert("L").point(lambda p: p < 200 and 255).getbbox()
        # La concentración va en una segunda línea.
        self.assertGreater(caja[3], 25)


class PhrasesCatalogTest(SimpleTestCase):
    def tearDown(self):
        phrases_catalog.set_phrase_resolver(None)

    def test_lookup_y_resolvedor(self):
        phrases_catalog.set_phrase_resolver(None)
        self.assertIsNone(phrases_catalog.lookup(""))
        self.assertIsNone(phrases_catalog.lookup("H999"))
        phrases_catalog.set_phrase_resolver(lambda code: "Desde la base" if code == "H999" else None)
        self.assertEqual(phrases_catalog.lookup("h999"), "Desde la base")
        phrases_catalog.set_phrase_resolver(mock.Mock(side_effect=RuntimeError))
        # Si el resolvedor falla se usa el catálogo local.
        self.assertEqual(phrases_catalog.lookup("H314"), phrases_catalog.H_PHRASES["H314"])

    def test_expand_item(self):
        phrases_catalog.set_phrase_resolver(None)
        self.assertEqual(phrases_catalog.expand_item("Texto libre"), "Texto libre")
        self.assertEqual(phrases_catalog.expand_item("H999"), "H999")
        # Combinación no oficial: se expande cada parte si todas son conocidas.
        self.assertEqual(
            phrases_catalog.expand_item("H200+H201", with_code=False),
            phrases_catalog.H_PHRASES["H200"] + " " + phrases_catalog.H_PHRASES["H201"],
        )
        self.assertEqual(phrases_catalog.expand_item("H200+H999"), "H200+H999")

    def test_is_code(self):
        self.assertTrue(phrases_catalog.is_code("P305 + P351"))
        self.assertFalse(phrases_catalog.is_code("Use guantes"))


class PlannerHelpersTest(SimpleTestCase):
    def test_combine_codes(self):
        self.assertEqual(planner_mod._combine_codes(""), "")
        self.assertEqual(planner_mod._combine_codes("sin códigos"), "sin códigos")
        self.assertEqual(planner_mod._combine_codes("H314 H315 H316 H318 P280"), "H314-H316 H318 P280")

    def test_phrase_codes_str_con_combinaciones(self):
        self.assertEqual(
            planner_mod._phrase_codes_str(["P280 Use guantes", "P305+P351 Lavar", "texto"]),
            "P280 P305+P351",
        )

    def test_phrase_block_height_con_fds(self):
        plan = LabelPlanner._make_plan(10, 10, 4, ["a"], [], ["fds"])
        self.assertEqual(LabelPlanner._phrase_block_height(plan), 12 + 4 + 12)


class FitPhraseBlockTest(SimpleTestCase):
    """Cascada de degradación de frases: cada fase según el alto disponible."""

    def setUp(self):
        self.planner = LabelPlanner()
        self.m = Measurer(self.planner.resources, dpi=300)
        self.h = ["H300", "H310", "H330", "H314"]
        self.p = ["P260", "P264", "P280", "P301+P310"]

    def fit(self, avail, h=None, p=None, width=600):
        return self.planner._fit_phrase_block(
            self.m, self.h if h is None else h, self.p if p is None else p, width, avail, 400, 300
        )

    def test_sin_frases(self):
        plan = self.fit(10, h=[], p=[])
        self.assertEqual((plan["h_lines"], plan["p_lines"], plan["fds_lines"]), ([], [], []))

    def test_fases_de_degradacion(self):
        completo = self.fit(100000)
        self.assertFalse(completo["fds_lines"])
        self.assertTrue(any("Mortal" in ln for ln in completo["h_lines"]))
        lh = self.m.line_height(self.m.font(LabelPlanner._min_phrase_font(self.m, 300, 400)))
        resultados = {}
        for avail in range(4000, 0, -5):
            plan = self.fit(avail)
            h_texto = any("Mortal" in ln for ln in plan["h_lines"])
            clave = (h_texto, bool(plan["p_lines"]), bool(plan["fds_lines"]), len(plan["h_lines"]))
            resultados.setdefault(clave, avail)
        fases = {(h, p, f) for h, p, f, _ in resultados}
        self.assertIn((True, True, True), fases)    # H completo + P en códigos + FDS
        self.assertIn((True, False, True), fases)   # H completo + FDS
        self.assertIn((False, True, True), fases)   # H códigos + P códigos + FDS
        self.assertIn((False, False, True), fases)  # H códigos (o truncados) + FDS
        self.assertGreater(lh, 0)

    def test_sin_consejos_omite_fds_en_fase_h_completo(self):
        planes = [self.fit(avail, p=[]) for avail in range(800, 0, -5)]
        self.assertTrue(any(p["h_lines"] and not p["fds_lines"] for p in planes))
        self.assertTrue(any(p["fds_lines"] for p in planes))

    def test_truncado_ultimo_recurso(self):
        plan = self.fit(0, width=50)
        self.assertEqual(len(plan["h_lines"]), 1)
        self.assertTrue("".join(plan["fds_lines"]).replace(" ", "").startswith("ConsultelaFDS"))


class PlannerLayoutTest(SimpleTestCase):
    def test_cabecera_con_catedra_laboratorio_y_sin_logos(self):
        bp = _blueprint(
            catedra="QUÍMICA ORGÁNICA",
            laboratorio="L-101",
            institucion="UNIVERSIDAD NACIONAL DE COSTA RICA, SEDE REGIONAL CHOROTEGA, CAMPUS NICOYA " * 3,
            logo_izq_path="/no/existe.png",
        )
        layout = _plan(bp)
        cabecera = _cajas(layout, "text")[0].content_ref
        self.assertEqual(cabecera["lines"][1:], ["CÁTEDRA DE QUÍMICA ORGÁNICA", "Laboratorio L-101"])
        # Sin logo izquierdo solo queda un logo y el texto se encoge para caber.
        self.assertEqual(len(_cajas(layout, "logo")), 1)
        normal = _cajas(_plan(_blueprint()), "text")[0].content_ref
        self.assertLess(cabecera["font_size"], normal["font_size"])

    def test_formula_concentracion_y_estado(self):
        bp = _blueprint(formula="H_{2}SO_{4}", concentracion="98 %", estado_fisico="s")
        layout = _plan(bp)
        self.assertEqual(_cajas(layout, "name")[0].content_ref["suffix"], "(s)")
        self.assertEqual(_cajas(layout, "formula")[0].content_ref["concentracion"], "98 %")

    def test_nombre_en_blanco(self):
        layout = _plan(_blueprint(nombre="   "))
        self.assertEqual(_cajas(layout, "name")[0].content_ref["lines"], [])

    def test_palabra_bajo_los_pictogramas_con_nombre_largo(self):
        largo = "Hidróxido de tetrametilamonio pentahidratado"
        sin_pictos = _plan(_blueprint(35, 20, nombre=largo, simbolos=[]))
        con_pictos = _plan(_blueprint(35, 20, nombre=largo, simbolos=["Corrosivo", "Tóxico", "Inflamable"]))
        for layout in (sin_pictos, con_pictos):
            palabra = [b for b in _cajas(layout, "text") if b.content_ref["lines"] == ["PELIGRO"]]
            self.assertEqual(len(palabra), 1)
            self.assertEqual(palabra[0].content_ref["color"], config.BORDER_COLORS["PELIGRO"])

    def test_palabra_al_lado_de_los_pictogramas(self):
        layout = _plan(_blueprint(35, 40, nombre="Hidróxido de tetrametilamonio pentahidratado", palabra_advertencia="Atención"))
        palabra = [b for b in _cajas(layout, "text") if b.content_ref["lines"] == ["Atención"]][0]
        picto = _cajas(layout, "pictogram")[0]
        self.assertGreater(palabra.x, picto.x + picto.width)
        self.assertEqual(palabra.content_ref["color"], config.BORDER_COLORS["ATENCION"])

    def test_pictogramas_epp_bajo_el_qr(self):
        layout = _plan(_blueprint(simbolos=["Corrosivo", EPP_SIMBOLO, "iso 7010 m010"]))
        qr = _cajas(layout, "qr")[0]
        epp = [b for b in _cajas(layout, "pictogram") if b.content_ref["symbol"].startswith("iso")]
        self.assertEqual(len(epp), 2)
        for caja in epp:
            self.assertGreater(caja.y, qr.y + qr.height - 1)

    def test_pie_preparador_info_y_caducidad(self):
        bp = _blueprint(
            100, 80,
            fabricante="Merck",
            responsable="Ana Pérez",
            info_adicional="Mantener refrigerado. " * 60,
            fecha_caducidad="01/01/2030",
            lote="L-1234567890",
            cantidad="2500 mL",
            ubicacion="Bodega principal, estante superior izquierdo, gaveta 4",
        )
        textos = _textos(_plan(bp))
        self.assertIn("Fabricante: Merck", textos)
        self.assertIn("Preparador: Ana Pérez", textos)
        self.assertTrue(any(t.startswith("Mantener refrigerado.") for t in textos))
        self.assertTrue(any("Caducidad: 01/01/2030" in t for t in textos))
        # El pie no cabe en una línea y se parte.
        self.assertTrue(any(t.startswith("Ubicación:") for t in textos))

    def test_cuerpo_escalado_para_caber(self):
        def alto_pila(self, ctx, scale):
            return 10 ** 6 if scale > 0.85 else 0

        with mock.patch.object(LabelPlanner, "_top_stack_height", alto_pila):
            with mock.patch.object(engine_mod.logger, "warning") as warning:
                LabelEngine().generate(_blueprint())
        warning.assert_any_call("layout: %s", "cuerpo escalado a 0.85 para caber")

    def test_contenido_obligatorio_que_no_cabe(self):
        with mock.patch.object(LabelPlanner, "_top_stack_height", return_value=10 ** 6):
            with self.assertRaisesMessage(LabelTooSmallError, "insuficiente para el contenido obligatorio"):
                _plan(_blueprint())

    def test_fit_font_width_encoge(self):
        m = Measurer()
        fs = LabelPlanner._fit_font_width(m, "PELIGRO", 40, 60)
        self.assertLess(fs, 60)
        self.assertLessEqual(m.text_width("PELIGRO", m.font(fs, bold=True)), 40)


class EngineTest(SimpleTestCase):
    def test_elemento_sin_renderer_se_omite(self):
        engine = LabelEngine()
        del engine.renderers["qr"]
        with mock.patch.object(engine_mod.logger, "warning") as warning:
            img = engine.generate(_blueprint())
        self.assertEqual(img.mode, "RGB")
        warning.assert_any_call("Sin renderer para element_type=%s", "qr")


class PdfTest(SimpleTestCase):
    def _paginas(self, path):
        with open(path, "rb") as f:
            contenido = f.read()
        self.assertTrue(contenido.startswith(b"%PDF"))
        return contenido.count(b"/Type /Page\n") or contenido.count(b"/Type /Page ")

    def test_generate_pdf_salta_de_pagina(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "etiquetas.pdf")
            generate_pdf([_blueprint(120, 80, dpi=60) for _ in range(4)], path, "A4")
            self.assertEqual(self._paginas(path), 2)

    def test_labels_to_pdf_desde_dicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "etiquetas.pdf")
            labels_to_pdf([{"nombre": "Agua"}, {"nombre": "Etanol"}], path)
            self.assertEqual(self._paginas(path), 1)
