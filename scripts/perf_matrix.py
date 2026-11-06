#!/usr/bin/env python3
"""Compara configuraciones de ejecución de la suite: tiempo, CPU y RSS pico.

    python scripts/perf_matrix.py                 # todas (horas: lanzar en segundo plano)
    python scripts/perf_matrix.py --only unit     # solo la suite sin navegador
    python scripts/perf_matrix.py --only selenium --label sel-w4
    python scripts/perf_matrix.py --list

Cada corrida va con prioridad baja (nice/ionice). Las de Selenium van SIEMPRE dentro
de `xvfb-run`: nunca abren ventanas en la pantalla del usuario. El RSS pico se muestrea
cada segundo sobre todo el árbol de procesos (workers, chromedriver, Chrome, Xvfb).

Escribe/actualiza `roadmap/.perf/matrix.json`, que lee `manage.py perf_report`.
"""

import argparse
import json
import os
import re
import resource
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "roadmap" / ".perf" / "matrix.json"
LOGS = ROOT / "roadmap" / ".perf" / "matrix-logs"
PYTHON = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable

LOW_PRIORITY = ["nice", "-n", "10", "ionice", "-c3"]
XVFB = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1280x720x24"]
TEST = [PYTHON, "manage.py", "test", "--no-input"]

# (suite, etiqueta, argumentos extra, variables de entorno)
CONFIGS = [
    ("unit", "unit-serial", ["--exclude-tag=selenium", "--parallel", "1"], {}),
    ("unit", "unit-p2", ["--exclude-tag=selenium", "--parallel", "2"], {}),
    ("unit", "unit-p4", ["--exclude-tag=selenium", "--parallel", "4"], {}),
    ("unit", "unit-p8", ["--exclude-tag=selenium", "--parallel", "8"], {}),
    ("unit", "unit-p4-keepdb", ["--exclude-tag=selenium", "--parallel", "4", "--keepdb"], {}),
    ("selenium", "sel-w2", ["--tag=selenium", "--parallel", "2"], {"GENERATE_SCREENSHOTS": "False"}),
    ("selenium", "sel-w4", ["--tag=selenium", "--parallel", "4"], {"GENERATE_SCREENSHOTS": "False"}),
    ("selenium", "sel-w6", ["--tag=selenium", "--parallel", "6"], {"GENERATE_SCREENSHOTS": "False"}),
    ("selenium", "sel-w4-gif", ["--tag=selenium", "--parallel", "4"], {"GENERATE_SCREENSHOTS": "True"}),
]
# Sin `--keepdb` en Selenium: deja la base sin permisos y loaddata revienta en setUpClass.


def tree_rss_kb(root):
    total = 0
    try:
        procs = [root] + root.children(recursive=True)
    except psutil.Error:
        return 0
    for proc in procs:
        try:
            total += proc.memory_info().rss
        except psutil.Error:
            pass
    return total // 1024


def run(suite, label, extra, env_extra):
    command = LOW_PRIORITY + TEST + extra
    if suite == "selenium":
        command = XVFB + command
    env = dict(os.environ, **env_extra)
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / ("%s.log" % label)

    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.perf_counter()
    peak = 0
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(command, cwd=SRC, env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        root = psutil.Process(proc.pid)
        stop = threading.Event()

        def sample():
            nonlocal peak
            while not stop.is_set():
                peak = max(peak, tree_rss_kb(root))
                stop.wait(1.0)

        sampler = threading.Thread(target=sample, daemon=True)
        sampler.start()
        code = proc.wait()
        stop.set()
        sampler.join()
    wall = time.perf_counter() - start
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)

    text = log_path.read_text(encoding="utf-8", errors="replace")
    ran = re.findall(r"^Ran (\d+) tests? in", text, re.M)
    status = re.findall(r"^(OK.*|FAILED \(.*\))$", text, re.M)
    return {
        "suite": suite,
        "label": label,
        "command": " ".join(command),
        "tests": int(ran[-1]) if ran else None,
        "wall_s": round(wall, 1),
        "cpu_s": round(cpu, 1),
        "rss_peak_kb": peak,
        "exit": code,
        "result": status[-1] if status else "exit %d" % code,
        "log": str(log_path.relative_to(ROOT)),
    }


def pick_best(runs):
    """La más rápida de cada suite entre las que terminaron con el mismo nº de pruebas que la mayoría."""
    best = {}
    for suite in sorted({r["suite"] for r in runs}):
        candidates = [r for r in runs if r["suite"] == suite and r["tests"]]
        if not candidates:
            continue
        counts = [r["tests"] for r in candidates]
        usual = max(set(counts), key=counts.count)
        candidates = [r for r in candidates if r["tests"] == usual]
        fastest = min(candidates, key=lambda r: r["wall_s"])
        lightest = min(candidates, key=lambda r: r["rss_peak_kb"])
        why = "%.0f s, %.0f MiB pico" % (fastest["wall_s"], fastest["rss_peak_kb"] / 1024.0)
        if lightest is not fastest:
            why += "; la más liviana es `%s` (%.0f s, %.0f MiB)" % (
                lightest["label"], lightest["wall_s"], lightest["rss_peak_kb"] / 1024.0)
        best[suite] = {"label": fastest["label"], "why": why}
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=("unit", "selenium"))
    parser.add_argument("--label", action="append", help="solo estas etiquetas (se puede repetir)")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    configs = [c for c in CONFIGS if (not args.only or c[0] == args.only)
               and (not args.label or c[1] in args.label)]
    if args.list:
        for suite, label, extra, env in configs:
            print("%-9s %-16s %s %s" % (suite, label, " ".join(extra), env or ""))
        return

    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"runs": []}
    for suite, label, extra, env in configs:
        print("== %s" % label, flush=True)
        result = run(suite, label, extra, env)
        print("   %(wall_s)s s, CPU %(cpu_s)s s, RSS pico %(rss_peak_kb)s KiB, %(result)s" % result, flush=True)
        # Una corrida nueva reemplaza la anterior con la misma etiqueta.
        data["runs"] = [r for r in data["runs"] if r["label"] != label] + [result]
        data["best"] = pick_best(data["runs"])
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
