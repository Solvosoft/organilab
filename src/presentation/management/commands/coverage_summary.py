# encoding: utf-8
"""Resume el JSON de coverage en un Markdown por app.

    python manage.py coverage_summary                     # resumen en pantalla
    python manage.py coverage_summary -o roadmap/COBERTURA.md
    python manage.py coverage_summary --json otro.json --top 60

El JSON sale de `make coverage-combine` (unitarias + Selenium ya unidas).
"""

import json
import subprocess
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


def default_json():
    return Path(settings.BASE_DIR).parent / "roadmap" / ".coverage" / "coverage.json"


def _pct(covered, total):
    return 100.0 * covered / total if total else 100.0


def summarize(data):
    """Devuelve (totales, por_app, por_archivo) a partir del JSON de coverage."""
    apps = defaultdict(lambda: {"statements": 0, "missing": 0, "files": 0})
    files = []
    for name, info in data["files"].items():
        summary = info["summary"]
        app = Path(name).parts[0] if len(Path(name).parts) > 1 else "(raíz)"
        apps[app]["statements"] += summary["num_statements"]
        apps[app]["missing"] += summary["missing_lines"]
        apps[app]["files"] += 1
        files.append({
            "file": name,
            "app": app,
            "statements": summary["num_statements"],
            "missing": summary["missing_lines"],
            "percent": summary["percent_covered"],
        })
    totals = data["totals"]
    return totals, dict(apps), files


class Command(BaseCommand):
    help = "Resumen de cobertura por app y archivos con más líneas sin cubrir"

    def add_arguments(self, parser):
        parser.add_argument("--json", help="JSON de coverage (por defecto roadmap/.coverage/coverage.json)")
        parser.add_argument("--top", type=int, default=40, help="cuántos archivos listar")
        parser.add_argument("-o", "--output", help="fichero destino (por defecto, stdout)")

    def handle(self, *args, **options):
        path = Path(options["json"] or default_json())
        if not path.exists():
            raise CommandError("no existe %s: correr antes `make coverage-all`" % path)
        data = json.loads(path.read_text(encoding="utf-8"))
        content = self.render(data, options["top"])

        if options["output"]:
            Path(options["output"]).write_text(content, encoding="utf-8")
            self.stdout.write("escrito %s" % options["output"])
        else:
            self.stdout.write(content)

    def render(self, data, top):
        totals, apps, files = summarize(data)
        lines = [
            "# Cobertura de código",
            "",
            "Generado con `make coverage-all` (suite sin navegador + Selenium headless, unidas con "
            "`coverage combine`). No editar a mano: `make coverage-summary` lo regenera.",
            "",
            "- Fecha: %s" % timezone.localtime().strftime("%Y-%m-%d %H:%M"),
            "- Commit: `%s`" % self._commit(),
            "- **Total: %.1f%%** — %d sentencias, %d sin cubrir, %d archivos" % (
                totals["percent_covered"], totals["num_statements"], totals["missing_lines"], len(files)),
            "",
            "## Por app",
            "",
            "| App | Archivos | Sentencias | Sin cubrir | Cobertura |",
            "|-----|---------:|-----------:|-----------:|----------:|",
        ]
        ordered = sorted(apps.items(), key=lambda item: -item[1]["missing"])
        for app, info in ordered:
            covered = info["statements"] - info["missing"]
            lines.append("| `%s` | %d | %d | %d | %.1f%% |" % (
                app, info["files"], info["statements"], info["missing"], _pct(covered, info["statements"])))

        lines += [
            "",
            "## Archivos con más líneas sin cubrir (top %d)" % top,
            "",
            "| Archivo | Sentencias | Sin cubrir | Cobertura |",
            "|---------|-----------:|-----------:|----------:|",
        ]
        for entry in sorted(files, key=lambda f: -f["missing"])[:top]:
            if not entry["missing"]:
                break
            lines.append("| `%s` | %d | %d | %.1f%% |" % (
                entry["file"], entry["statements"], entry["missing"], entry["percent"]))

        never = [f for f in files if f["statements"] and f["missing"] == f["statements"]]
        lines += [
            "",
            "## Archivos nunca ejecutados (%d)" % len(never),
            "",
            "Candidatos a código muerto antes que a pruebas nuevas.",
            "",
        ]
        for entry in sorted(never, key=lambda f: f["file"]):
            lines.append("- `%s` (%d sentencias)" % (entry["file"], entry["statements"]))
        return "\n".join(lines) + "\n"

    def _commit(self):
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], cwd=settings.BASE_DIR, text=True).strip()
        except Exception:
            return "?"
