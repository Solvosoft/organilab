# encoding: utf-8
"""Emite el inventario de rutas clasificadas.

    python manage.py url_inventory                       # resumen en pantalla
    python manage.py url_inventory --format md -o fichero
    python manage.py url_inventory --category pagina --coverage
    python manage.py url_inventory --check               # ¿el fichero está al día?
"""

import csv
import io
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

from presentation.url_inventory import (
    CATEGORIES,
    annotate_coverage,
    build_inventory,
    counts_by_category,
)

COLUMNS = (
    "namespace", "nombre", "patrón", "vista", "archivo:línea", "categoría",
    "plantilla", "kwargs", "selenium", "pruebas",
)


class Command(BaseCommand):
    help = "Inventario de rutas clasificadas (página, api, ajax, descarga, …)"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("resumen", "md", "csv"), default="resumen")
        parser.add_argument("--category", choices=CATEGORIES, help="filtra por categoría")
        parser.add_argument("--namespace", help="filtra por namespace, p. ej. laboratory")
        parser.add_argument("--coverage", action="store_true",
                            help="cruza con los reverse() de las pruebas")
        parser.add_argument("-o", "--output", help="fichero destino (por defecto, stdout)")
        parser.add_argument("--check", metavar="FICHERO",
                            help="compara con FICHERO y sale con error si difiere")

    def handle(self, *args, **options):
        entries = build_inventory()
        if options["coverage"] or options["format"] == "md" or options["check"]:
            annotate_coverage(entries)

        if options["category"]:
            entries = [e for e in entries if e.category == options["category"]]
        if options["namespace"]:
            entries = [e for e in entries if e.namespace == options["namespace"]]

        if options["check"]:
            return self._check(entries, options["check"])

        renderer = {
            "resumen": self._render_summary,
            "md": self._render_markdown,
            "csv": self._render_csv,
        }[options["format"]]
        content = renderer(entries)

        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as handle:
                handle.write(content)
            self.stdout.write("escrito %s (%d rutas)" % (options["output"], len(entries)))
        else:
            self.stdout.write(content)

    # -- comprobación ------------------------------------------------------

    def _check(self, entries, path):
        expected = self._render_markdown(entries)
        try:
            with open(path, encoding="utf-8") as handle:
                current = handle.read()
        except OSError as exc:
            raise CommandError("no se pudo leer %s: %s" % (path, exc))
        if current != expected:
            raise CommandError(
                "%s está desactualizado. Regeneralo con `make url-inventory`." % path
            )
        self.stdout.write("%s está al día (%d rutas)" % (path, len(entries)))

    # -- salidas -----------------------------------------------------------

    def _render_summary(self, entries):
        counts = counts_by_category(entries)
        lines = ["%d rutas con nombre" % len(entries), ""]
        for category in CATEGORIES:
            if counts.get(category):
                lines.append("  %-13s %4d" % (category, counts[category]))
        unknown = [e for e in entries if e.category == "desconocida"]
        if unknown:
            lines += ["", "sin clasificar:"]
            lines += ["  %s → %s" % (e.full_name, e.view) for e in unknown]
        duplicated = sorted({e.full_name for e in entries if e.duplicated})
        if duplicated:
            lines += ["", "nombres duplicados (reverse devuelve la última):"]
            lines += ["  %s" % name for name in duplicated]
        return "\n".join(lines) + "\n"

    def _render_markdown(self, entries):
        counts = counts_by_category(entries)
        pages = [e for e in entries if e.category == "pagina"]
        uncovered = [e for e in pages if not (e.covered_selenium or e.covered_tests)]

        out = io.StringIO()
        out.write("# Inventario de rutas\n\n")
        out.write("Generado por `make url-inventory`. No editar a mano: se regenera.\n\n")
        out.write("Clasifica cada ruta con nombre por lo que **es**, para poder decidir con\n")
        out.write("qué se prueba. Las de categoría `pagina` son las que un navegador visita;\n")
        out.write("el resto se cubre con pruebas de cliente o unitarias.\n\n")

        out.write("## Resumen\n\n| Categoría | Rutas |\n|---|---:|\n")
        for category in CATEGORIES:
            if counts.get(category):
                out.write("| `%s` | %d |\n" % (category, counts[category]))
        out.write("| **total** | **%d** |\n\n" % len(entries))
        out.write("Páginas: %d, de las cuales **%d sin ninguna prueba**.\n\n"
                  % (len(pages), len(uncovered)))

        duplicated = sorted({e.full_name for e in entries if e.duplicated})
        if duplicated:
            out.write("## Nombres duplicados\n\n")
            out.write("`reverse()` devuelve la última registrada; la otra es ruta muerta.\n\n")
            for name in duplicated:
                for entry in entries:
                    if entry.full_name == name:
                        out.write("- `%s` → `%s` (%s)\n" % (name, entry.pattern, entry.source))
            out.write("\n")

        # Las de `api` e `infra` se cuentan pero no se listan: son 1.400 filas de
        # routers DRF y de la administración de Django que no se prueban con
        # navegador y solo estorbarían aquí. Están completas en el CSV.
        listed = [e for e in entries if e.category not in ("api", "infra")]
        by_app = defaultdict(list)
        for entry in listed:
            by_app[entry.app].append(entry)

        out.write("## Rutas por app\n\n")
        out.write("Se omiten las categorías `api` e `infra` (%d rutas de routers DRF y de\n"
                  "la administración de Django): están en `inventario_urls.csv`.\n\n"
                  % (len(entries) - len(listed)))
        for app in sorted(by_app):
            rows = sorted(by_app[app], key=lambda e: (e.category, e.name))
            page_count = sum(1 for e in rows if e.category == "pagina")
            gaps = sum(1 for e in rows
                       if e.category == "pagina"
                       and not (e.covered_selenium or e.covered_tests))
            out.write("### %s — %d páginas, %d sin prueba\n\n" % (app, page_count, gaps))
            out.write("| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |\n")
            out.write("|---|---|---|---|---|---|:-:|:-:|\n")
            for entry in rows:
                out.write("| `%s` | `%s` | %s | `%s` | %s | %s | %s | %s |\n" % (
                    entry.name,
                    entry.pattern,
                    entry.category,
                    entry.view,
                    "`%s`" % entry.template if entry.template else "—",
                    ", ".join(entry.kwargs) or "—",
                    "sí" if entry.covered_selenium else "—",
                    "sí" if entry.covered_tests else "—",
                ))
            out.write("\n")
        return out.getvalue()

    def _render_csv(self, entries):
        out = io.StringIO()
        # lineterminator explícito: el \r\n por defecto de csv deja el fichero
        # con CRLF y git lo normaliza después, dejándolo distinto de lo que
        # genera el comando.
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(COLUMNS)
        for entry in entries:
            writer.writerow([
                entry.namespace, entry.name, entry.pattern, entry.view, entry.source,
                entry.category, entry.template, "|".join(entry.kwargs),
                int(entry.covered_selenium), int(entry.covered_tests),
            ])
        return out.getvalue()
