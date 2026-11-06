# encoding: utf-8
"""La instrumentación de rendimiento mide sin participar.

Igual que la sonda de roles: apagada no puede cambiar nada, encendida deja una línea
por petición o prueba, y los comandos que la resumen leen lo que ella escribe.
"""

import io
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from presentation import perf


class PerfDirMixin:
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        patcher = mock.patch.object(perf, "output_dir", return_value=self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Los handles abiertos apuntan a otra carpeta: cada prueba empieza de cero.
        perf._handles.clear()
        self.addCleanup(perf._handles.clear)

    def lines(self, kind):
        rows = []
        for path in self.folder.glob("%s-*.jsonl" % kind):
            rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        return rows


class PerfMiddlewareTest(PerfDirMixin, TestCase):
    def get_response(self, request):
        User.objects.count()
        User.objects.exists()
        return HttpResponse("hola")

    def test_apagada_no_escribe_nada(self):
        with mock.patch.dict(os.environ, {perf.ENV_FLAG: "0"}):
            middleware = perf.PerfMiddleware(self.get_response)
            response = middleware(RequestFactory().get("/"))
        self.assertEqual(response.content, b"hola")
        self.assertEqual(self.lines("request"), [])

    def test_encendida_anota_la_peticion(self):
        with mock.patch.dict(os.environ, {perf.ENV_FLAG: "1"}):
            middleware = perf.PerfMiddleware(self.get_response)
            response = middleware(RequestFactory().get("/algo/"))
        self.assertEqual(response.status_code, 200)
        [row] = self.lines("request")
        self.assertEqual(row["method"], "GET")
        self.assertEqual(row["status"], 200)
        self.assertEqual(row["queries"], 2)
        self.assertEqual(row["bytes"], 4)
        for campo in ("wall_ms", "cpu_ms", "sql_ms"):
            self.assertGreaterEqual(row[campo], 0)
        self.assertNotIn("mem_peak_kb", row)

    def test_con_memoria_anota_el_pico(self):
        env = {perf.ENV_FLAG: "1", perf.MEM_FLAG: "1"}
        with mock.patch.dict(os.environ, env):
            middleware = perf.PerfMiddleware(lambda request: HttpResponse("x" * 100000))
            middleware(RequestFactory().get("/"))
        [row] = self.lines("request")
        self.assertGreater(row["mem_peak_kb"], 0)

    def test_un_fallo_al_anotar_no_tumba_la_peticion(self):
        with mock.patch.dict(os.environ, {perf.ENV_FLAG: "1"}), \
                mock.patch.object(perf, "write", side_effect=RuntimeError):
            middleware = perf.PerfMiddleware(self.get_response)
            response = middleware(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 200)


class PerfTestHookTest(PerfDirMixin, SimpleTestCase):
    def test_la_medicion_por_prueba_anota_y_atribuye(self):
        visto = {}

        def original(test, result, debug=False):
            visto["test"] = perf.get_current_test()

        class Falsa:
            tags = set()

            def id(self):
                return "app.tests.Falsa.test_x"

        perf._measure_test(original)(Falsa(), None)

        self.assertEqual(visto["test"], "app.tests.Falsa.test_x")
        self.assertIsNone(perf.get_current_test())
        [row] = self.lines("test")
        self.assertEqual(row["test"], "app.tests.Falsa.test_x")
        self.assertFalse(row["selenium"])
        self.assertIsNone(row["browser_rss_kb"])

    def test_rss_lee_proc(self):
        rss, hwm = perf.rss_kb()
        if Path("/proc/self/status").exists():
            self.assertGreater(rss, 0)
            self.assertGreaterEqual(hwm, rss)


class PerfReportCommandTest(PerfDirMixin, SimpleTestCase):
    def write_rows(self, kind, rows):
        with open(self.folder / ("%s-1.jsonl" % kind), "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")

    def test_resume_peticiones_pruebas_y_clases(self):
        base = {"method": "GET", "status": 200, "cpu_ms": 1, "sql_ms": 1, "bytes": 10, "test": None}
        self.write_rows("request", [
            dict(base, urlname="lab:lenta", wall_ms=900, queries=120),
            dict(base, urlname="lab:lenta", wall_ms=1000, queries=10),
            dict(base, urlname="lab:rapida", wall_ms=5, queries=1),
        ])
        self.write_rows("test", [{
            "test": "a.b.C.test_x", "selenium": True, "wall_s": 3.0, "cpu_s": 1.0,
            "rss_before_kb": 1000, "rss_after_kb": 3048, "browser_rss_kb": 204800,
        }])
        self.write_rows("class", [
            {"class": "a.b.C", "phase": "setup", "wall_s": 2.5, "cpu_s": 1, "rss_kb": 1},
            {"class": "a.b.C", "phase": "teardown", "wall_s": 0.5, "cpu_s": 1, "rss_kb": 1},
        ])
        out = io.StringIO()
        call_command("perf_report", dir=str(self.folder), stdout=out)
        texto = out.getvalue()

        lenta = texto.index("`lab:lenta`")
        self.assertLess(lenta, texto.index("`lab:rapida`"), "la más lenta va primero")
        self.assertIn("| 10–120 |", texto)
        self.assertIn("⚠", texto)
        self.assertIn("`a.b.C.test_x`", texto)
        self.assertIn("| 200.0 |", texto)  # RSS del navegador en MiB
        self.assertIn("| `a.b.C` | 1 | 2.5 | 0.5 |", texto)
        self.assertIn("make perf-matrix", texto)
        self.assertIn("make perf-reports", texto)


class CoverageSummaryCommandTest(SimpleTestCase):
    def test_resume_por_app_y_lista_los_nunca_ejecutados(self):
        data = {
            "totals": {"percent_covered": 50.0, "num_statements": 40, "missing_lines": 20},
            "files": {
                "laboratory/views.py": {"summary": {"num_statements": 30, "missing_lines": 10, "percent_covered": 66.7}},
                "sga/muerto.py": {"summary": {"num_statements": 10, "missing_lines": 10, "percent_covered": 0.0}},
            },
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(data, handle)
        self.addCleanup(os.unlink, handle.name)

        out = io.StringIO()
        call_command("coverage_summary", json=handle.name, stdout=out)
        texto = out.getvalue()

        self.assertIn("**Total: 50.0%**", texto)
        self.assertIn("| `laboratory` | 1 | 30 | 10 | 66.7% |", texto)
        self.assertIn("## Archivos nunca ejecutados (1)", texto)
        self.assertIn("- `sga/muerto.py` (10 sentencias)", texto)
