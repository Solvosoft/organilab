# encoding: utf-8
"""Instrumentación de rendimiento para la suite de pruebas.

Mide **cuánto cuesta** cada petición y cada prueba, al estilo de la sonda de roles
(`presentation/probe.py`): apagada por defecto, se enciende con `ORGANILAB_PERF=1`
y escribe JSONL por proceso en `roadmap/.perf/`. `make perf-report` lo resume.

Qué se anota:

* **Petición** (`PerfMiddleware`, primera de `MIDDLEWARE`): ruta, método, status, tiempo de pared, CPU del hilo,
  consultas SQL (cantidad y tiempo) y tamaño de la respuesta.
* **Prueba** (parche de `SimpleTestCase._setup_and_call`): duración, CPU del proceso,
  RSS antes/después y, si la prueba es Selenium, RSS del navegador.
* **Clase** (`setUpClass`/`tearDownClass`): carga de fixtures y arranque del navegador.

Pasadas aparte, porque distorsionan los tiempos:

* `ORGANILAB_PERF_MEM=1` — pico de `tracemalloc` por petición. El pico es global al
  proceso: con peticiones concurrentes es una cota superior, no un valor exacto.
* `ORGANILAB_PERF_PROFILE=1` — cProfile agregado por ruta, volcado como `.prof`.
"""

import atexit
import cProfile
import json
import os
import pstats
import resource
import threading
import time
from pathlib import Path

from django.conf import settings

ENV_FLAG = "ORGANILAB_PERF"
MEM_FLAG = "ORGANILAB_PERF_MEM"
PROFILE_FLAG = "ORGANILAB_PERF_PROFILE"

# Una prueba a la vez por proceso: a diferencia de `probe` (threading.local) esto lo ve
# también el hilo del live server, así las peticiones de Selenium quedan atribuidas.
_current_test = None
_lock = threading.Lock()
_handles = {}
_profiles = {}
_dirty_profiles = set()
_installed = False


def is_enabled():
    return os.environ.get(ENV_FLAG) == "1"


def mem_enabled():
    return is_enabled() and os.environ.get(MEM_FLAG) == "1"


def profile_enabled():
    return is_enabled() and os.environ.get(PROFILE_FLAG) == "1"


def output_dir():
    # Las pasadas de memoria y de perfil escriben aparte (ver Makefile) para no mezclar
    # tiempos inflados con los de la pasada normal.
    custom = os.environ.get("ORGANILAB_PERF_DIR")
    path = Path(custom) if custom else Path(getattr(settings, "BASE_DIR")).parent / "roadmap" / ".perf"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_test():
    return _current_test


def write(kind, entry):
    """Añade una línea al JSONL `<kind>-<pid>.jsonl`. Nunca lanza."""
    try:
        entry["pid"] = os.getpid()
        line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
        with _lock:
            key = (kind, os.getpid())
            handle = _handles.get(key)
            if handle is None:
                handle = open(output_dir() / ("%s-%d.jsonl" % (kind, os.getpid())), "a", encoding="utf-8")
                _handles[key] = handle
            handle.write(line)
            handle.flush()
    except Exception:
        pass


def rss_kb(pid="self"):
    """RSS actual y pico (VmHWM) en KiB leyendo /proc; (None, None) si no hay /proc."""
    rss = hwm = None
    try:
        with open("/proc/%s/status" % pid, encoding="ascii") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1])
                elif line.startswith("VmHWM:"):
                    hwm = int(line.split()[1])
    except OSError:
        pass
    return rss, hwm


def browser_rss_kb(test):
    """RSS sumado de chromedriver y sus hijos (Chrome) si la prueba tiene navegador."""
    driver = getattr(test, "selenium", None)
    service = getattr(driver, "service", None)
    process = getattr(service, "process", None)
    pid = getattr(process, "pid", None)
    if not pid:
        return None
    try:
        import psutil

        root = psutil.Process(pid)
        total = 0
        for proc in [root] + root.children(recursive=True):
            try:
                total += proc.memory_info().rss
            except psutil.Error:
                pass
        return total // 1024
    except Exception:
        return None


def _cpu_seconds():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


# -- petición ---------------------------------------------------------------

class _QueryCounter:
    def __init__(self):
        self.count = 0
        self.seconds = 0.0

    def __call__(self, execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.seconds += time.perf_counter() - start
            self.count += 1


class PerfMiddleware:
    """Mide cada petición. Va al principio de `MIDDLEWARE`: cubre toda la cadena."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = is_enabled()
        self.mem = mem_enabled()
        self.profile = profile_enabled()
        if self.mem:
            import tracemalloc

            if not tracemalloc.is_tracing():
                tracemalloc.start()

    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        from django.db import connection

        counter = _QueryCounter()
        profiler = cProfile.Profile() if self.profile else None
        if self.mem:
            import tracemalloc

            tracemalloc.reset_peak()
            mem_start = tracemalloc.get_traced_memory()[0]
        wall = time.perf_counter()
        cpu = time.thread_time()
        with connection.execute_wrapper(counter):
            if profiler:
                profiler.enable()
            try:
                response = self.get_response(request)
            finally:
                if profiler:
                    profiler.disable()
        cpu = time.thread_time() - cpu
        wall = time.perf_counter() - wall

        try:
            match = getattr(request, "resolver_match", None)
            urlname = match.view_name if match and match.view_name else None
            entry = {
                "urlname": urlname,
                "path": request.path if urlname is None else None,
                "method": request.method,
                "status": getattr(response, "status_code", None),
                "wall_ms": round(wall * 1000, 2),
                "cpu_ms": round(cpu * 1000, 2),
                "queries": counter.count,
                "sql_ms": round(counter.seconds * 1000, 2),
                "bytes": None if getattr(response, "streaming", False) else len(response.content),
                "test": get_current_test(),
            }
            if self.mem:
                import tracemalloc

                entry["mem_peak_kb"] = (tracemalloc.get_traced_memory()[1] - mem_start) // 1024
            write("request", entry)
            if profiler:
                _add_profile(urlname or "(sin-ruta)", profiler)
        except Exception:
            # Igual que la sonda: mide, no participa.
            pass
        return response


def _add_profile(urlname, profiler):
    with _lock:
        stats = _profiles.get(urlname)
        if stats is None:
            _profiles[urlname] = pstats.Stats(profiler)
        else:
            stats.add(profiler)
        _dirty_profiles.add(urlname)


def flush_profiles():
    """Vuelca a disco los perfiles que cambiaron.

    Se llama al terminar cada prueba y en `atexit`: los workers de `--parallel` mueren
    con `Pool.terminate()` y en ellos `atexit` no llega a correr.
    """
    with _lock:
        dirty = list(_dirty_profiles)
        _dirty_profiles.clear()
        if not dirty:
            return
        folder = output_dir() / "profiles"
        folder.mkdir(exist_ok=True)
        for urlname in dirty:
            safe = urlname.replace(":", "__").replace("/", "_")
            try:
                _profiles[urlname].dump_stats(folder / ("%s-%d.prof" % (safe, os.getpid())))
            except Exception:
                pass


atexit.register(flush_profiles)


# -- prueba y clase -----------------------------------------------------------

def _failures(result):
    """Errores + fallos acumulados. En `--parallel` el resultado es un `RemoteTestResult`,
    cuyas listas son `DummyList` sin `len()`: ahí se cuentan sus eventos."""
    if result is None:
        return 0
    try:
        return len(result.errors) + len(result.failures)
    except TypeError:
        return sum(1 for event in getattr(result, "events", ()) if event[0] in ("addError", "addFailure"))


def _measure_test(original):
    def _setup_and_call(self, result, debug=False):
        global _current_test
        test_id = self.id()
        _current_test = test_id
        try:
            from presentation import probe

            probe.set_current_test(test_id)
        except Exception:
            pass
        rss_before, _ = rss_kb()
        cpu = _cpu_seconds()
        wall = time.perf_counter()
        errors = _failures(result)
        try:
            return original(self, result, debug)
        finally:
            # Medir jamás puede tumbar la prueba.
            try:
                _record_test(self, test_id, wall, cpu, rss_before, _failures(result) > errors)
            except Exception:
                pass
            _current_test = None
            flush_profiles()

    return _setup_and_call


def _record_test(self, test_id, wall, cpu, rss_before, failed):
    wall = time.perf_counter() - wall
    cpu = _cpu_seconds() - cpu
    rss_after, hwm = rss_kb()
    write("test", {
        "test": test_id,
        "class": "%s.%s" % (type(self).__module__, type(self).__qualname__),
        "selenium": "selenium" in getattr(self, "tags", set()) or hasattr(type(self), "selenium"),
        "wall_s": round(wall, 3),
        "cpu_s": round(cpu, 3),
        "rss_before_kb": rss_before,
        "rss_after_kb": rss_after,
        "rss_hwm_kb": hwm,
        "browser_rss_kb": browser_rss_kb(self),
        "failed": failed,
    })


def _measure_class_hook(original, phase):
    def hook(suite, test, result):
        previous = getattr(result, "_previousTestClass", None)
        current = test.__class__ if test is not None else None
        # unittest llama a ambos ganchos en cada prueba; solo hay trabajo al cambiar de clase.
        changed = current != previous
        cls = current if phase == "setup" else previous
        name = "%s.%s" % (cls.__module__, cls.__qualname__) if cls is not None else None
        wall = time.perf_counter()
        cpu = _cpu_seconds()
        try:
            return original(suite, test, result)
        finally:
            wall = time.perf_counter() - wall
            if name and changed:
                write("class", {
                    "class": name,
                    "phase": phase,
                    "wall_s": round(wall, 3),
                    "cpu_s": round(_cpu_seconds() - cpu, 3),
                    "rss_kb": rss_kb()[0],
                })

    return hook


def install():
    """Parchea la medición por prueba y por clase. Idempotente; nada si está apagada."""
    global _installed
    if _installed or not is_enabled():
        return
    import unittest.suite

    from django.test import SimpleTestCase

    SimpleTestCase._setup_and_call = _measure_test(SimpleTestCase._setup_and_call)
    suite = unittest.suite.TestSuite
    suite._handleClassSetUp = _measure_class_hook(suite._handleClassSetUp, "setup")
    suite._tearDownPreviousClass = _measure_class_hook(suite._tearDownPreviousClass, "teardown")
    _install_celery()
    _installed = True


# -- tareas Celery --------------------------------------------------------------

_task_starts = {}


def _task_prerun(task_id=None, task=None, **kwargs):
    _task_starts[task_id] = (time.perf_counter(), _cpu_seconds(), rss_kb()[0])


def _task_postrun(task_id=None, task=None, state=None, **kwargs):
    start = _task_starts.pop(task_id, None)
    if start is None:
        return
    wall, cpu, rss_before = start
    write("task", {
        "task": getattr(task, "name", None),
        "state": state,
        "wall_s": round(time.perf_counter() - wall, 3),
        "cpu_s": round(_cpu_seconds() - cpu, 3),
        "rss_before_kb": rss_before,
        "rss_after_kb": rss_kb()[0],
        "test": get_current_test(),
    })


def _install_celery():
    try:
        from celery import signals
    except ImportError:
        return
    signals.task_prerun.connect(_task_prerun, weak=False)
    signals.task_postrun.connect(_task_postrun, weak=False)


# -- runner ---------------------------------------------------------------------

from django.test.runner import ParallelTestSuite  # noqa: E402

from presentation.probe import ProbeRunner  # noqa: E402


class PerfParallelTestSuite(ParallelTestSuite):
    # Django la invoca como función suelta (`self.process_setup.__func__(*args)`) y
    # solo con el método de arranque `spawn`; con `fork` el parche ya viene heredado.
    def process_setup(*args):
        install()


class PerfRunner(ProbeRunner):
    """`ProbeRunner` más la medición de rendimiento. Apagada, es `ProbeRunner` tal cual."""

    parallel_test_suite = PerfParallelTestSuite

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        install()
