# encoding: utf-8
"""Resume las mediciones de `presentation/perf.py` en `roadmap/RENDIMIENTO.md`.

    python manage.py perf_report                       # resumen en pantalla
    python manage.py perf_report -o roadmap/RENDIMIENTO.md --json roadmap/rendimiento.json

Fuentes, todas en `roadmap/.perf/`:

* `request-*.jsonl`, `test-*.jsonl`, `class-*.jsonl` — `make perf`.
* `mem/request-*.jsonl` — `make perf-mem`.
* `profiles/*.prof` — `make perf-profile`.
* `matrix.json` — `make perf-matrix` (configuraciones de ejecución).
* `reports.json` — `make perf-reports` (reportes contra volumen de datos).
"""

import json
import os
import platform
import pstats
import subprocess
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

# Más consultas que esto en una sola petición es candidato a N+1.
MANY_QUERIES = 50


def perf_dir():
    return Path(settings.BASE_DIR).parent / "roadmap" / ".perf"


def read_jsonl(folder, kind):
    rows = []
    for path in sorted(folder.glob("%s-*.jsonl" % kind)):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(pct / 100.0 * (len(ordered) - 1)))))
    return ordered[index]


def aggregate_requests(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get("urlname") or row.get("path") or "?", row.get("method"))].append(row)
    result = []
    for (urlname, method), items in groups.items():
        walls = [r["wall_ms"] for r in items]
        queries = [r["queries"] for r in items]
        mems = [r["mem_peak_kb"] for r in items if r.get("mem_peak_kb") is not None]
        sizes = [r["bytes"] for r in items if r.get("bytes") is not None]
        result.append({
            "urlname": urlname,
            "method": method,
            "n": len(items),
            "p50_ms": round(percentile(walls, 50), 1),
            "p95_ms": round(percentile(walls, 95), 1),
            "max_ms": round(max(walls), 1),
            "cpu_p95_ms": round(percentile([r["cpu_ms"] for r in items], 95), 1),
            "queries_max": max(queries),
            "queries_min": min(queries),
            "sql_p95_ms": round(percentile([r["sql_ms"] for r in items], 95), 1),
            "mem_peak_kb": max(mems) if mems else None,
            "bytes_max": max(sizes) if sizes else None,
            "total_s": round(sum(walls) / 1000.0, 2),
            "statuses": sorted({str(r.get("status")) for r in items}),
        })
    return result


def aggregate_profiles(folder, names, limit=8):
    """Para cada ruta, las funciones del proyecto con más tiempo acumulado.

    Ordenar por tiempo propio solo muestra psycopg y `getattr`; lo accionable es qué
    función de `src/` arrastra ese tiempo (cumtime).
    """
    result = {}
    prof_dir = folder / "profiles"
    if not prof_dir.exists():
        return result
    project = str(Path(settings.BASE_DIR)) + "/"
    for urlname in names:
        safe = urlname.replace(":", "__").replace("/", "_")
        files = sorted(prof_dir.glob("%s-*.prof" % safe))
        if not files:
            continue
        stats = pstats.Stats(str(files[0]))
        for extra in files[1:]:
            stats.add(str(extra))
        rows = []
        for (filename, line, func), (cc, nc, tt, ct, callers) in stats.stats.items():
            if filename.startswith(project) and "/site-packages/" not in filename and not _wrapper(filename, func):
                rows.append((ct, tt, nc, "%s:%d(%s)" % (_short(filename), line, func)))
        rows.sort(reverse=True)
        result[urlname] = [
            {"tottime_s": round(tt, 3), "cumtime_s": round(ct, 3), "calls": nc, "where": where}
            for ct, tt, nc, where in rows[:limit]
        ]
    return result


def _wrapper(filename, func):
    """Capas que solo envuelven la vista: su cumtime es el de toda la petición."""
    if filename.endswith(("presentation/perf.py", "presentation/probe.py")):
        return True
    return filename.endswith("middleware.py") and func == "__call__"


def _short(filename):
    for marker in ("site-packages/", "/src/"):
        if marker in filename:
            return filename.split(marker, 1)[1]
    return filename


def _mb(kb):
    return "—" if kb is None else "%.1f" % (kb / 1024.0)


class Command(BaseCommand):
    help = "Informe de rendimiento a partir de roadmap/.perf/"

    def add_arguments(self, parser):
        parser.add_argument("--dir", help="carpeta de mediciones (por defecto roadmap/.perf)")
        parser.add_argument("--top", type=int, default=25)
        parser.add_argument("-o", "--output", help="Markdown destino (por defecto, stdout)")
        parser.add_argument("--json", help="además, un resumen JSON versionable")

    def handle(self, *args, **options):
        folder = Path(options["dir"] or perf_dir())
        if not folder.exists():
            raise CommandError("no existe %s: correr antes `make perf`" % folder)
        top = options["top"]

        requests = aggregate_requests(read_jsonl(folder, "request"))
        # La memoria sale de su propia pasada (`make perf-mem`): tracemalloc infla los tiempos.
        mem_requests = aggregate_requests(read_jsonl(folder / "mem", "request")) if (folder / "mem").exists() else []
        tests = read_jsonl(folder, "test")
        classes = read_jsonl(folder, "class")
        matrix = self._load(folder / "matrix.json")
        reports = self._load(folder / "reports.json")
        slow = sorted(requests, key=lambda r: -r["p95_ms"])[:top]
        profiles = aggregate_profiles(folder, [r["urlname"] for r in slow[:10]])

        summary = {
            "fecha": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
            "commit": self._commit(),
            "maquina": "%s, %s núcleos, Python %s" % (platform.machine(), os.cpu_count(), platform.python_version()),
            "peticiones": sum(r["n"] for r in requests),
            "rutas": len(requests),
            "pruebas": len(tests),
            "vistas_lentas": slow,
            "vistas_consultas": sorted(requests, key=lambda r: -r["queries_max"])[:top],
            "vistas_memoria": sorted([r for r in mem_requests + requests if r["mem_peak_kb"] is not None],
                                     key=lambda r: -r["mem_peak_kb"])[:top],
            "vistas_tiempo_total": sorted(requests, key=lambda r: -r["total_s"])[:top],
            "pruebas_lentas": sorted(tests, key=lambda t: -t["wall_s"])[:top],
            "pruebas_memoria": sorted(tests, key=lambda t: -((t.get("rss_after_kb") or 0) - (t.get("rss_before_kb") or 0)))[:top],
            "pruebas_navegador": sorted([t for t in tests if t.get("browser_rss_kb")],
                                        key=lambda t: -t["browser_rss_kb"])[:top],
            "clases_setup": self._classes(classes)[:top],
            "perfiles": profiles,
            "matriz": matrix,
            "reportes": reports,
        }

        content = self.render(summary)
        if options["output"]:
            Path(options["output"]).write_text(content, encoding="utf-8")
            self.stdout.write("escrito %s" % options["output"])
        else:
            self.stdout.write(content)
        if options["json"]:
            Path(options["json"]).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
            self.stdout.write("escrito %s" % options["json"])

    # -- datos ---------------------------------------------------------------

    def _load(self, path):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def _classes(self, rows):
        groups = defaultdict(lambda: {"setup_s": 0.0, "teardown_s": 0.0, "n": 0})
        for row in rows:
            group = groups[row["class"]]
            group["%s_s" % row["phase"]] += row["wall_s"]
            if row["phase"] == "setup":
                group["n"] += 1
        result = [dict(clase=name, **values) for name, values in groups.items()]
        for item in result:
            item["setup_s"] = round(item["setup_s"], 2)
            item["teardown_s"] = round(item["teardown_s"], 2)
        return sorted(result, key=lambda c: -(c["setup_s"] + c["teardown_s"]))

    def _commit(self):
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], cwd=settings.BASE_DIR, text=True).strip()
        except Exception:
            return "?"

    # -- Markdown --------------------------------------------------------------

    def render(self, s):
        out = [
            "# Rendimiento de Organilab",
            "",
            "Generado con `make perf-report` a partir de `roadmap/.perf/`. No editar a mano.",
            "Los tiempos son de la suite de pruebas (base pequeña, live server de Django): sirven "
            "para **comparar** vistas entre sí, no como latencia de producción.",
            "",
            "- Fecha: %s · commit `%s` · %s" % (s["fecha"], s["commit"], s["maquina"]),
            "- %d peticiones medidas sobre %d rutas; %d pruebas." % (s["peticiones"], s["rutas"], s["pruebas"]),
            "",
        ]
        out += self._section_views(s)
        out += self._section_tests(s)
        out += self._section_reports(s["reportes"])
        out += self._section_matrix(s["matriz"])
        return "\n".join(out) + "\n"

    def _section_views(self, s):
        out = [
            "## Vistas más lentas (p95)",
            "",
            "| Ruta | Método | n | p50 ms | p95 ms | máx ms | CPU p95 ms | SQL p95 ms | consultas máx |",
            "|------|--------|--:|-------:|-------:|-------:|-----------:|-----------:|--------------:|",
        ]
        for r in s["vistas_lentas"]:
            out.append("| `%s` | %s | %d | %s | %s | %s | %s | %s | %d |" % (
                r["urlname"], r["method"], r["n"], r["p50_ms"], r["p95_ms"], r["max_ms"],
                r["cpu_p95_ms"], r["sql_p95_ms"], r["queries_max"]))
        out += [
            "",
            "## Vistas con más consultas SQL",
            "",
            "Más de %d consultas en una petición, o un rango min–máx amplio entre peticiones de la "
            "misma ruta, sugiere N+1 (consultas que crecen con los datos)." % MANY_QUERIES,
            "",
            "| Ruta | Método | n | consultas min–máx | SQL p95 ms | N+1? |",
            "|------|--------|--:|------------------:|-----------:|:----:|",
        ]
        for r in s["vistas_consultas"]:
            suspect = r["queries_max"] > MANY_QUERIES or (r["queries_max"] - r["queries_min"]) > MANY_QUERIES / 2
            out.append("| `%s` | %s | %d | %d–%d | %s | %s |" % (
                r["urlname"], r["method"], r["n"], r["queries_min"], r["queries_max"], r["sql_p95_ms"],
                "⚠" if suspect else ""))
        if s["vistas_memoria"]:
            out += [
                "",
                "## Vistas con más memoria (pico tracemalloc)",
                "",
                "| Ruta | Método | n | pico MiB | respuesta máx KiB |",
                "|------|--------|--:|---------:|------------------:|",
            ]
            for r in s["vistas_memoria"]:
                out.append("| `%s` | %s | %d | %s | %s |" % (
                    r["urlname"], r["method"], r["n"], _mb(r["mem_peak_kb"]),
                    "—" if r["bytes_max"] is None else r["bytes_max"] // 1024))
        out += [
            "",
            "## Tiempo total acumulado por ruta",
            "",
            "Dónde se va el tiempo de la suite: una ruta barata pero muy llamada pesa más que una cara llamada una vez.",
            "",
            "| Ruta | Método | n | total s | p50 ms |",
            "|------|--------|--:|--------:|-------:|",
        ]
        for r in s["vistas_tiempo_total"]:
            out.append("| `%s` | %s | %d | %s | %s |" % (r["urlname"], r["method"], r["n"], r["total_s"], r["p50_ms"]))
        if s["perfiles"]:
            out += ["", "## Funciones calientes del proyecto (cProfile, vistas más lentas)", "",
                    "Funciones de `src/` por tiempo acumulado (incluye lo que llaman: ORM, plantillas).", ""]
            for urlname, rows in s["perfiles"].items():
                out += ["### `%s`" % urlname, "", "| cumtime s | tottime s | llamadas | dónde |",
                        "|----------:|----------:|---------:|-------|"]
                for row in rows:
                    out.append("| %s | %s | %s | `%s` |" % (row["cumtime_s"], row["tottime_s"], row["calls"], row["where"]))
                out.append("")
        out.append("")
        return out

    def _section_tests(self, s):
        out = [
            "## Pruebas más lentas",
            "",
            "| Prueba | Selenium | s | CPU s | RSS después MiB |",
            "|--------|:--------:|--:|------:|----------------:|",
        ]
        for t in s["pruebas_lentas"]:
            out.append("| `%s` | %s | %s | %s | %s |" % (
                t["test"], "✓" if t.get("selenium") else "", t["wall_s"], t["cpu_s"], _mb(t.get("rss_after_kb"))))
        out += [
            "",
            "## Pruebas que más memoria dejan en el proceso",
            "",
            "Crecimiento de RSS durante la prueba (lo que no se libera se acumula en el worker).",
            "",
            "| Prueba | Δ RSS MiB | RSS después MiB |",
            "|--------|----------:|----------------:|",
        ]
        for t in s["pruebas_memoria"]:
            delta = (t.get("rss_after_kb") or 0) - (t.get("rss_before_kb") or 0)
            out.append("| `%s` | %s | %s |" % (t["test"], _mb(delta), _mb(t.get("rss_after_kb"))))
        if s["pruebas_navegador"]:
            out += ["", "## Memoria del navegador (chromedriver + Chrome)", "",
                    "| Prueba | RSS navegador MiB |", "|--------|------------------:|"]
            for t in s["pruebas_navegador"]:
                out.append("| `%s` | %s |" % (t["test"], _mb(t["browser_rss_kb"])))
        out += [
            "",
            "## Clases con setUpClass/tearDownClass más caros",
            "",
            "Fixtures, arranque del navegador, live server. Se paga una vez por clase y por worker.",
            "",
            "| Clase | veces | setUp s | tearDown s |",
            "|-------|------:|--------:|-----------:|",
        ]
        for c in s["clases_setup"]:
            out.append("| `%s` | %d | %s | %s |" % (c["clase"], c["n"], c["setup_s"], c["teardown_s"]))
        out.append("")
        return out

    def _section_reports(self, reports):
        if not reports:
            return ["## Reportes contra volumen de datos", "", "_Sin datos: correr `make perf-reports`._", ""]
        out = [
            "## Reportes contra volumen de datos",
            "",
            "Cada reporte registrado, generado con la base sembrada a varias escalas "
            "(`seed_volume`). «Crecimiento» compara la escala mayor con la menor frente al "
            "crecimiento de los datos: > 1 es superlineal.",
            "",
            "| Reporte | Formato | Escala | filas base | s | consultas | pico MiB | archivo KiB | estado |",
            "|---------|---------|-------:|-----------:|--:|----------:|---------:|------------:|--------|",
        ]
        for r in reports.get("runs", []):
            out.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r["report"], r["format"], r["scale"], r.get("rows", "—"), r.get("wall_s", "—"),
                r.get("queries", "—"), _mb(r.get("mem_peak_kb")),
                "—" if r.get("bytes") is None else r["bytes"] // 1024, r.get("status", "")))
        growth = reports.get("growth") or []
        if growth:
            out += ["", "| Reporte | Formato | crecimiento tiempo | crecimiento memoria | veredicto |",
                    "|---------|---------|-------------------:|--------------------:|-----------|"]
            for g in growth:
                out.append("| `%s` | %s | %s | %s | %s |" % (
                    g["report"], g["format"], g["time_ratio"], g["mem_ratio"], g["verdict"]))
        out.append("")
        return out

    def _section_matrix(self, matrix):
        if not matrix:
            return ["## Configuraciones de ejecución", "", "_Sin datos: correr `make perf-matrix`._", ""]
        out = [
            "## Configuraciones de ejecución",
            "",
            "Cada fila es una corrida completa; RSS pico suma todo el árbol de procesos (workers, "
            "Chrome, Xvfb).",
            "",
            "| Suite | Configuración | pruebas | s | CPU s | RSS pico MiB | resultado |",
            "|-------|---------------|--------:|--:|------:|-------------:|-----------|",
        ]
        for r in matrix.get("runs", []):
            out.append("| %s | `%s` | %s | %s | %s | %s | %s |" % (
                r["suite"], r["label"], r.get("tests", "—"), r["wall_s"], r["cpu_s"],
                _mb(r["rss_peak_kb"]), r.get("result", "")))
        for suite, best in (matrix.get("best") or {}).items():
            out.append("")
            out.append("**Mejor para %s:** `%s` — %s" % (suite, best["label"], best["why"]))
        out.append("")
        return out
