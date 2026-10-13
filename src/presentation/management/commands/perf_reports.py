# encoding: utf-8
"""Genera cada reporte registrado con la base sembrada a varias escalas y mide su costo.

    python manage.py perf_reports --settings=organilab.test_settings --scales 1,10,100
    python manage.py perf_reports --settings=organilab.test_settings --scales 1,2 --only report_objects
    python manage.py perf_reports --settings=organilab.test_settings --scales 1 --formats html,xlsx --keepdb

Trabaja en una base **aislada** (`test_organilab_perf`), creada con las migraciones y
`laboratory_data.json` como las pruebas, y la borra al final salvo `--keepdb`. Nunca
toca la base de desarrollo.

Cada reporte corre en un proceso hijo con tope de tiempo (`--timeout`) y de memoria
(`--mem-limit`): uno que no escala se anota como «tiempo» o «memoria» y no se vuelve a
intentar en escalas mayores, en vez de colgar la máquina.

Resultado en `roadmap/.perf/reports.json`, que lee `manage.py perf_report`.
"""

import json
import os
import resource
import signal
import tempfile
import time
import traceback
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.test.utils import setup_databases, teardown_databases

from presentation import perf_volume
from report import register

PERF_DB = "test_organilab_perf"
SPREADSHEETS = ("xlsx", "ods", "xls")


class _Timeout(Exception):
    pass


def default_formats(entry):
    """html (dataset), una hoja de cálculo y pdf: los tres caminos de código distintos."""
    formats = [f for f in ("html",) if f in entry]
    sheet = next((f for f in SPREADSHEETS if f in entry), None)
    if sheet:
        formats.append(sheet)
    if "pdf" in entry:
        formats.append("pdf")
    return formats


def rss_kb():
    with open("/proc/self/status", encoding="ascii") as handle:
        values = {}
        for line in handle:
            if line.startswith(("VmRSS:", "VmHWM:", "VmSize:")):
                key, value = line.split(":", 1)
                values[key] = int(value.split()[0])
    return values


class Command(BaseCommand):
    help = "Reportes contra volumen de datos: tiempo, consultas y memoria por escala"

    def add_arguments(self, parser):
        parser.add_argument("--scales", default="1,10,100", help="unidades de escala acumuladas, p. ej. 1,10,100")
        parser.add_argument("--only", action="append", help="solo estos reportes (se puede repetir)")
        parser.add_argument("--formats", help="formatos a medir (por defecto html, una hoja y pdf)")
        parser.add_argument("--timeout", type=int, default=300, help="segundos por reporte")
        parser.add_argument("--mem-limit", type=int, default=4096, help="MiB adicionales por reporte")
        parser.add_argument("--keepdb", action="store_true", help="conservar test_organilab_perf al terminar")
        parser.add_argument("-o", "--output", help="JSON destino (por defecto roadmap/.perf/reports.json)")

    def handle(self, *args, **options):
        if not getattr(settings, "TESTING_MODE", False):
            raise CommandError("usar con --settings=organilab.test_settings")
        scales = sorted({int(s) for s in options["scales"].split(",") if s.strip()})
        reports = options["only"] or list(register.REPORT_FORMS)
        unknown = set(reports) - set(register.REPORT_FORMS)
        if unknown:
            raise CommandError("reportes desconocidos: %s" % ", ".join(sorted(unknown)))
        output = Path(options["output"] or Path(settings.BASE_DIR).parent / "roadmap" / ".perf" / "reports.json")

        connections["default"].settings_dict.setdefault("TEST", {})["NAME"] = PERF_DB
        settings.MEDIA_ROOT = tempfile.mkdtemp(prefix="organilab-perf-media-")
        # Solo `default`: `oldDB` existe en settings y crear su base de prueba borraría la
        # que pudiera estar usando otra corrida.
        old_config = setup_databases(verbosity=1, interactive=False, keepdb=options["keepdb"], aliases={"default"})
        try:
            call_command("loaddata", "laboratory_data.json", verbosity=0)
            runs = self.measure(scales, reports, options)
        finally:
            if not options["keepdb"]:
                connections.close_all()
                teardown_databases(old_config, verbosity=1)

        data = {"scales": scales, "runs": runs, "growth": growth(runs)}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        self.stdout.write("escrito %s" % output)

    def measure(self, scales, reports, options):
        from laboratory.models import Laboratory

        runs = []
        seeded = 0
        given_up = set()
        for scale in scales:
            started = time.perf_counter()
            perf_volume.seed(scale - seeded, start=seeded)
            seeded = scale
            size = perf_volume.data_size()
            self.stdout.write("== escala %d: %s (sembrado en %.0f s)" % (scale, size, time.perf_counter() - started))
            labs = list(Laboratory.objects.filter(organization_id=perf_volume.ORG_PK).values_list("pk", flat=True))
            for name in reports:
                entry = register.REPORT_FORMS[name]
                formats = options["formats"].split(",") if options["formats"] else default_formats(entry)
                for file_type in formats:
                    if file_type not in entry:
                        continue
                    row = {"report": name, "format": file_type, "scale": scale, "rows": size["shelfobjects"]}
                    if (name, file_type) in given_up:
                        row["status"] = "omitido (no escaló antes)"
                    else:
                        row.update(self.run_child(name, file_type, labs, options))
                        if row["status"] in ("tiempo", "memoria"):
                            given_up.add((name, file_type))
                    self.stdout.write("   %-36s %-5s %s" % (name, file_type, _line(row)))
                    runs.append(row)
        return runs

    def run_child(self, name, file_type, labs, options):
        """Corre un reporte en un proceso hijo con topes; devuelve sus medidas."""
        # El hijo no puede heredar la conexión: cerrarla allí mandaría el Terminate por
        # el socket compartido y rompería la del padre.
        connections.close_all()
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:  # pragma: no cover - corre en el hijo
            os.close(read_fd)
            result = self.child(name, file_type, labs, options)
            with os.fdopen(write_fd, "w") as pipe:
                pipe.write(json.dumps(result, default=str))
            os._exit(0)

        os.close(write_fd)
        deadline = time.monotonic() + options["timeout"] + 30
        status = None
        while time.monotonic() < deadline:
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                break
            time.sleep(0.2)
        else:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        with os.fdopen(read_fd) as pipe:
            raw = pipe.read()
        if raw:
            return json.loads(raw)
        if status is not None and os.WIFSIGNALED(status):
            return {"status": "memoria" if os.WTERMSIG(status) == signal.SIGKILL else "señal %d" % os.WTERMSIG(status)}
        return {"status": "tiempo"}

    def child(self, name, file_type, labs, options):  # pragma: no cover - corre en el hijo
        from django.contrib.auth.models import User

        from presentation.perf import _QueryCounter
        from report.models import ObjectChangeLogReport, TaskReport
        from report.views.base import build_report

        start_mem = rss_kb()
        limit = (start_mem["VmSize"] + options["mem_limit"] * 1024) * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

        def on_alarm(signum, frame):
            raise _Timeout()

        signal.signal(signal.SIGALRM, on_alarm)
        signal.alarm(options["timeout"])
        result = {}
        try:
            report = TaskReport.objects.create(
                created_by=User.objects.get(pk=perf_volume.USER_PK), type_report=name, file_type=file_type,
                data=perf_volume.payload(name, file_type, labs), language="es")
            counter = _QueryCounter()
            wall = time.perf_counter()
            cpu = time.process_time()
            with connections["default"].execute_wrapper(counter):
                build_report(report.pk, "http://127.0.0.1:9/")
            signal.alarm(0)
            report.refresh_from_db()
            if report.file:
                size = report.file.size
            elif report.table_content:
                size = len(json.dumps(report.table_content))
            else:
                # El HTML de cambios de objetos no usa `table_content`: deja
                # sus filas en ObjectChangeLogReport y la página las lee de ahí.
                rows = ObjectChangeLogReport.objects.filter(task_report=report).count()
                size = rows or None
            result = {
                "wall_s": round(time.perf_counter() - wall, 2),
                "cpu_s": round(time.process_time() - cpu, 2),
                "queries": counter.count,
                "sql_s": round(counter.seconds, 2),
                "mem_peak_kb": rss_kb()["VmHWM"] - start_mem["VmRSS"],
                "bytes": size,
                "status": "ok" if size else "vacío",
            }
        except _Timeout:
            result = {"status": "tiempo"}
        except MemoryError:
            result = {"status": "memoria"}
        except Exception as error:
            result = {"status": "error: %s" % type(error).__name__,
                      "error": "".join(traceback.format_exception_only(type(error), error)).strip()[:300]}
        finally:
            signal.alarm(0)
        return result


def _line(row):
    if row.get("wall_s") is None:
        return row["status"]
    return "%(wall_s)ss %(queries)s consultas %(mem_peak_kb)s KiB %(status)s" % row


def growth(runs):
    """Crecimiento entre la escala menor y la mayor, normalizado por el crecimiento de datos."""
    result = []
    keys = sorted({(r["report"], r["format"]) for r in runs})
    for report, file_type in keys:
        rows = [r for r in runs if r["report"] == report and r["format"] == file_type]
        ok = [r for r in rows if r.get("status") in ("ok", "vacío") and r.get("wall_s") is not None]
        failed = [r for r in rows if r.get("status") in ("tiempo", "memoria")]
        if failed:
            first = min(failed, key=lambda r: r["scale"])
            result.append({"report": report, "format": file_type, "time_ratio": "—", "mem_ratio": "—",
                           "verdict": "no escala: %s a escala %d" % (first["status"], first["scale"])})
            continue
        if len(ok) < 2:
            continue
        low, high = ok[0], ok[-1]
        data_ratio = high["rows"] / float(low["rows"] or 1)
        time_ratio = (high["wall_s"] / max(low["wall_s"], 0.01)) / data_ratio
        mem_ratio = (max(high["mem_peak_kb"], 1) / float(max(low["mem_peak_kb"], 1))) / data_ratio
        if time_ratio > 1.5 or mem_ratio > 1.5:
            verdict = "superlineal"
        elif time_ratio > 0.5:
            verdict = "lineal"
        else:
            verdict = "sublineal"
        result.append({"report": report, "format": file_type, "time_ratio": round(time_ratio, 2),
                       "mem_ratio": round(mem_ratio, 2), "verdict": verdict})
    return result
