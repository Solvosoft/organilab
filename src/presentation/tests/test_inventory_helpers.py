"""Las piezas del inventario de rutas y del catálogo de funcionalidades, una por una.

`test_url_inventory.py` y `test_feature_catalog.py` prueban el resultado sobre el
resolutor real; aquí se ejercita cada rama de la cascada con vistas de mentira, para que
un cambio en la heurística falle en la regla que rompe y no en un conteo global.
"""
import json
import tempfile
from pathlib import Path
from unittest import mock

from django.http import HttpResponse
from django.shortcuts import render
from django.test import SimpleTestCase, override_settings
from django.views.generic import ListView, View

from presentation import feature_catalog as fc
from presentation import url_inventory as ui
from presentation.models import Tutorial
from presentation.url_inventory import UrlEntry


def vista_parcial(request):
    return render(request, "laboratory/dataconfig.html")


def vista_render_dinamico(request):
    return render(request, request.GET["plantilla"])


def vista_plantilla_inexistente(request):
    return render(request, "laboratory/no_existe_esta_plantilla.html")


def vista_muda(request):
    return HttpResponse("hola")


def entrada(name, namespace="", category="pagina", **kwargs):
    return UrlEntry(name=name, namespace=namespace, pattern="/x", view="v", source="", category=category, **kwargs)


class ListaSinSufijo(ListView):
    model = Tutorial
    template_name_suffix = ""


class VistaConModelo(View):
    model = Tutorial


class VistaPDF(View):
    template_name = "report/hazard_map_pdf.html"


class VistaFragmento(View):
    template_name = "laboratory/dataconfig.html"


class FuenteDeVistaTest(SimpleTestCase):

    def test_fuente_ilegible_o_sin_fichero(self):
        self.assertEqual(ui._source_of(len), "")
        with mock.patch.object(ui.inspect, "getsourcefile", return_value=None), \
                mock.patch.object(ui.inspect, "getsourcelines", return_value=([], 1)):
            self.assertEqual(ui._source_of(vista_muda), "")

    def test_fichero_fuera_del_repo_conserva_su_ruta(self):
        source = ui._source_of(json.dumps)
        self.assertTrue(source.endswith(":%s" % json.dumps.__code__.co_firstlineno), source)
        self.assertIn("json", source)

    def test_texto_fuente_de_un_builtin(self):
        self.assertEqual(ui._source_text(len), "")


class PlantillaCandidataTest(SimpleTestCase):

    def test_sufijo_por_la_jerarquia_de_clases(self):
        self.assertEqual(ui._template_candidates(ListaSinSufijo.as_view()), ["presentation/tutorial_list.html"])

    def test_sin_sufijo_no_hay_candidata(self):
        self.assertEqual(ui._template_candidates(VistaConModelo.as_view()), [])

    def test_cadena_de_extends_vacia(self):
        self.assertEqual(ui._extends_chain(""), [])
        self.assertEqual(ui._extends_chain("base.html", depth=6), [])


class PermisosDeDecoradorTest(SimpleTestCase):

    def test_fuente_invalida(self):
        self.assertEqual(ui._decorator_permissions("def ("), [])

    def test_salta_lo_que_no_es_definicion(self):
        source = "x = 1\n@permission_required('app.ver')\ndef vista(request):\n    pass\n"
        self.assertEqual(ui._decorator_permissions(source), ["app.ver"])


class ClasificacionTest(SimpleTestCase):

    def test_autocomplete_por_modulo(self):
        def lookup(request):
            pass
        lookup.__module__ = "algo.gtselects"
        self.assertEqual(ui.classify(lookup, "algo:lookup", False)[0], "autocomplete")

    def test_plantilla_declarada_de_pdf_o_fragmento(self):
        self.assertEqual(ui.classify(VistaPDF.as_view(), "x:pdf", False)[0], "descarga")
        category, reason, template = ui.classify(VistaFragmento.as_view(), "x:frag", False)
        self.assertEqual((category, template), ("parcial", "laboratory/dataconfig.html"))
        self.assertIn("no llega a base.html", reason)

    def test_vistas_funcion_por_su_fuente(self):
        self.assertEqual(ui.classify(vista_parcial, "x:parcial", False),
                         ("parcial", "renderiza laboratory/dataconfig.html, que no llega a base.html",
                          "laboratory/dataconfig.html"))
        self.assertEqual(ui.classify(vista_render_dinamico, "x:dinamica", False)[0], "parcial")
        self.assertEqual(ui.classify(vista_muda, "x:muda", False)[0], "desconocida")
        # Una plantilla citada que no existe no aporta cadena de extends: se salta
        # y la vista cae en la regla genérica de render().
        self.assertEqual(ui.classify(vista_plantilla_inexistente, "x:inexistente", False)[0], "parcial")


class PaginasYCoberturaTest(SimpleTestCase):

    def test_paginas_filtradas_por_namespace(self):
        entries = [entrada("a", "uno"), entrada("b", "dos"), entrada("c", "uno", category="json")]
        self.assertEqual([e.name for e in ui.pages(entries)], ["a", "b"])
        self.assertEqual([e.name for e in ui.pages(entries, namespaces={"uno"})], ["a"])

    def test_ignora_ficheros_de_prueba_ilegibles(self):
        with tempfile.TemporaryDirectory() as root:
            tests = Path(root) / "app" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_roto.py").write_bytes(b"\xff\xfe\x00reverse('app:a')")
            (tests / "test_bueno.py").write_text("reverse('app:b')", encoding="utf-8")
            entries = ui.annotate_coverage([entrada("a", "app"), entrada("b", "app")], root=root)
        self.assertEqual([e.covered_tests for e in entries], [False, True])


class CatalogoHuerfanasTest(SimpleTestCase):

    def test_rutas_huerfanas_y_namespaces_pendientes(self):
        entries = [entrada("nadie", "app"), entrada("algo", "djgentelella"), entrada("api", "app", category="api")]
        self.assertEqual([e.full_name for e in fc.orphan_routes(entries, features=[])], ["app:nadie"])


class LecturaDeSondaTest(SimpleTestCase):

    def test_sin_directorio_no_hay_registros(self):
        with tempfile.TemporaryDirectory() as root, override_settings(BASE_DIR=Path(root) / "src"):
            self.assertEqual(fc.read_probe(), [])

    def test_lee_cada_jsonl_y_salta_lineas_rotas(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "probe-1.jsonl").write_text(
                '{"urlname": "a"}\n\nno es json\n{"urlname": "b"}\n', encoding="utf-8")
            (Path(root) / "otro.txt").write_text('{"urlname": "c"}\n', encoding="utf-8")
            self.assertEqual(fc.read_probe(root), [{"urlname": "a"}, {"urlname": "b"}])


class CoberturaPorRolTest(SimpleTestCase):

    def setUp(self):
        self.records = [
            {"urlname": None},
            {"urlname": "app:ver", "status": 200, "test": "t1", "roles": ["Estudiante", "Gestión de X"],
             "membership": "org_lab_user"},
            {"urlname": "app:super", "status": 200, "roles": ["superusuario"]},
            {"urlname": "app:negada", "status": 403, "roles": ["Estudiante"]},
            {"urlname": "app:fixture", "status": 200, "roles": ["Gestión de Y"]},
        ]
        self.steps = {
            name: fc.Step(name, name, actors=("estudiante", "profesor"), routes=routes)
            for name, routes in (("ver", ("app:ver",)), ("super", ("app:super",)),
                                 ("negada", ("app:negada",)), ("fixture", ("app:fixture",)),
                                 ("nunca", ("app:nunca",)), ("celery", ()))
        }
        self.feature = fc.Feature("f", "F", "app", "ui", "", tuple(self.steps.values()))

    def test_observaciones_por_ruta(self):
        observed = fc.observations_by_route(self.records)
        self.assertEqual(observed["app:ver"]["canonical"], {"estudiante"})
        self.assertEqual(observed["app:ver"]["fixture"], {"Gestión de X"})
        self.assertEqual(observed["app:ver"]["pseudo"], {"org_lab_user"})
        self.assertEqual(observed["app:ver"]["tests"], {"t1"})
        self.assertEqual(observed["app:super"]["pseudo"], {"superusuario"})
        self.assertNotIn(None, observed)

    def test_estado_de_cada_paso_y_huecos(self):
        report = fc.role_coverage([self.feature], self.records)
        states = {step.id: result["state"] for step, result in report["features"][0][1]}
        self.assertEqual(states, {
            "ver": fc.EXERCISED, "super": fc.ONLY_SUPERUSER, "negada": fc.ONLY_DENIED,
            "fixture": fc.ONLY_SUPERUSER, "nunca": fc.NEVER, "celery": "fuera del alcance de la sonda",
        })
        self.assertIn("f/ver", report["roles_exercised"]["estudiante"])
        self.assertNotIn("estudiante", [role.id for role in report["roles_never"]])

        gaps = {(step.id, actor) for _feature, step, actor, _state in fc.declared_but_not_exercised(report)}
        self.assertIn(("ver", "profesor"), gaps)
        self.assertNotIn(("ver", "estudiante"), gaps)
        self.assertFalse([gap for gap in gaps if gap[0] == "celery"])
