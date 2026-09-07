# encoding: utf-8
"""Emite el catálogo de funcionalidades y su cobertura.

    python manage.py feature_catalog                      # resumen en pantalla
    python manage.py feature_catalog --format md -o FICHERO
    python manage.py feature_catalog --sin-pruebas        # las que no prueba nadie
    python manage.py feature_catalog --roles              # el eje y quién lo ejercita
    python manage.py feature_catalog --huerfanas          # rutas sin funcionalidad
    python manage.py feature_catalog --check FICHERO      # ¿está al día?
"""

import io

from django.core.management.base import BaseCommand, CommandError

from presentation import feature_catalog as fc
from presentation.features import CATALOG_EXCLUDES, PENDING_NAMESPACES
from presentation.role_catalog import ALL_ROLES, CANONICAL_ROLES, PSEUDO_ROLES, get_role
from presentation.url_inventory import annotate_coverage, build_inventory


class Command(BaseCommand):
    help = "Catálogo de funcionalidades: pasos, actores y cobertura"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=("resumen", "md"), default="resumen")
        parser.add_argument("--module", help="filtra por app, p. ej. reservations_management")
        parser.add_argument("--kind", choices=("ui", "celery", "api"))
        parser.add_argument("--sin-pruebas", action="store_true", dest="untested")
        parser.add_argument("--roles", action="store_true")
        parser.add_argument("--huerfanas", action="store_true", dest="orphans")
        parser.add_argument("--ingest-probe", action="store_true", dest="ingest",
                            help="cruza lo que midió la sonda con el catálogo")
        parser.add_argument("--probe-dir", help="de dónde leer los JSONL de la sonda")
        parser.add_argument("-o", "--output")
        parser.add_argument("--check", metavar="FICHERO",
                            help="compara con FICHERO y sale con error si difiere")

    def handle(self, *args, **options):
        entries = annotate_coverage(build_inventory())
        features = fc.load_catalog()
        if options["module"]:
            features = tuple(f for f in features if f.module == options["module"])
        if options["kind"]:
            features = tuple(f for f in features if f.kind == options["kind"])

        if options["check"]:
            return self._check(features, entries, options["check"])
        if options["ingest"]:
            return self._ingest(features, options)
        if options["orphans"]:
            return self._print_orphans(features, entries)
        if options["untested"]:
            return self._print_untested(features, entries)
        if options["roles"]:
            return self._print_roles(features)

        renderer = self._render_markdown if options["format"] == "md" else self._render_summary
        content = renderer(features, entries)
        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as handle:
                handle.write(content)
            self.stdout.write("escrito %s (%d funcionalidades)"
                              % (options["output"], len(features)))
        else:
            self.stdout.write(content)

    # -- comprobación ------------------------------------------------------

    def _check(self, features, entries, path):
        expected = self._render_markdown(features, entries)
        try:
            with open(path, encoding="utf-8") as handle:
                current = handle.read()
        except OSError as exc:
            raise CommandError("no se pudo leer %s: %s" % (path, exc))
        if current != expected:
            raise CommandError(
                "%s está desactualizado. Regeneralo con `make feature-catalog`." % path
            )
        self.stdout.write("%s está al día (%d funcionalidades)" % (path, len(features)))

    # -- cobertura por rol -------------------------------------------------

    def _ingest(self, features, options):
        import json
        from pathlib import Path

        from django.conf import settings

        records = fc.read_probe(options.get("probe_dir"))
        if not records:
            raise CommandError(
                "la sonda no dejó nada en roadmap/.feature_probe/. "
                "¿Corriste `make feature-coverage`?"
            )
        report = fc.role_coverage(features, records)
        roadmap = Path(settings.BASE_DIR).parent / "roadmap"

        markdown = self._render_role_coverage(report, len(records))
        (roadmap / "COBERTURA_POR_ROL.md").write_text(markdown, encoding="utf-8")

        # El JSON es la línea base que el guardián compara: legible por máquina y
        # estable, para que un retroceso se vea en el diff.
        summary = {
            "peticiones_observadas": len(records),
            "roles_ejercitados": {
                role_id: sorted(pasos)
                for role_id, pasos in sorted(report["roles_exercised"].items())
            },
            "roles_nunca_ejercitados": [r.id for r in report["roles_never"]],
            "pasos": {
                "%s/%s" % (feature.id, step.id): result["state"]
                for feature, steps in report["features"]
                for step, result in steps
            },
        }
        (roadmap / "cobertura_por_rol.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        counts = {}
        for feature, steps in report["features"]:
            for _step, result in steps:
                counts[result["state"]] = counts.get(result["state"], 0) + 1
        self.stdout.write("%d peticiones observadas\n" % len(records))
        for state, total in sorted(counts.items()):
            self.stdout.write("  %-32s %d" % (state, total))
        self.stdout.write(
            "\n%d de %d roles canónicos sin ejercitar: %s"
            % (len(report["roles_never"]), len(CANONICAL_ROLES),
               ", ".join(r.name for r in report["roles_never"]) or "—")
        )
        self.stdout.write("\nescrito roadmap/COBERTURA_POR_ROL.md y cobertura_por_rol.json")

    def _render_role_coverage(self, report, total_records):
        out = io.StringIO()
        w = out.write
        w("# Cobertura por rol\n\n")
        w("Generado por `make feature-coverage`. No editar a mano: se regenera.\n\n")
        w("Esto **no** sale de leer las pruebas, sale de observarlas: la sonda de\n")
        w("`presentation/probe.py` anota cada petición HTTP de la suite con los `Rol`\n")
        w("que el usuario tenía en el ámbito de esa URL, resueltos con el mismo `Q` que\n")
        w("usa `ProfileMiddleware` para autorizar.\n\n")
        w("> **Una petición ejecutada por un superusuario no cuenta como cobertura de\n")
        w("> ningún rol.** El middleware se salta a los superusuarios\n")
        w("> (`authentication/middleware.py:49-50`), así que esa prueba ejercita la\n")
        w("> interacción, no el permiso.\n\n")
        w("Los `Rol` que solo existen en las fixtures —los «Gestión de X» de\n")
        w("`base_selenium.json`— tampoco cuentan: no existen en producción.\n\n")

        counts = {}
        for _feature, steps in report["features"]:
            for _step, result in steps:
                counts[result["state"]] = counts.get(result["state"], 0) + 1
        w("## Resumen\n\n| Estado del paso | Pasos |\n|---|---:|\n")
        for state, total in sorted(counts.items()):
            w("| %s | %d |\n" % (state, total))
        w("| **peticiones observadas** | **%d** |\n\n" % total_records)

        w("## Roles canónicos\n\n")
        w("| Rol | Pasos ejercitados |\n|---|---:|\n")
        exercised = report["roles_exercised"]
        for role in CANONICAL_ROLES:
            w("| %s | %d |\n" % (role.name, len(exercised.get(role.id, ()))))
        w("\n")
        if report["roles_never"]:
            w("**Sin ejercitar ni una vez:** %s.\n\n"
              % ", ".join(role.name for role in report["roles_never"]))

        w("## Pasos por funcionalidad\n\n")
        for feature, steps in report["features"]:
            w("### `%s` — %s\n\n" % (feature.id, feature.name))
            w("| Paso | Estado | Roles declarados | Roles observados |\n")
            w("|---|---|---|---|\n")
            for step, result in steps:
                declarados = ", ".join(
                    get_role(a).name for a in dict.fromkeys(step.actors)
                ) or "—"
                observados = ", ".join(
                    get_role(r).name for r in result["canonical"]
                ) or "—"
                w("| %s | %s | %s | %s |\n"
                  % (step.name, result["state"], declarados, observados))
            w("\n")

        gaps = fc.declared_but_not_exercised(report)
        w("## Lo que falta probar\n\n")
        w("Cada línea es un par (paso, rol) que el catálogo declara y la sonda no vio "
          "nunca: una prueba que falta, con su escenario ya escrito.\n\n")
        w("| Funcionalidad | Paso | Rol sin ejercitar | Estado del paso |\n")
        w("|---|---|---|---|\n")
        for feature, step, actor, state in gaps:
            w("| `%s` | %s | %s | %s |\n"
              % (feature.id, step.name, get_role(actor).name, state))
        w("\n")
        return out.getvalue()

    # -- vistas cortas -----------------------------------------------------

    def _print_orphans(self, features, entries):
        orphans = fc.orphan_routes(entries, features)
        self.stdout.write("%d rutas navegables sin funcionalidad\n" % len(orphans))
        for entry in orphans:
            self.stdout.write("  %-12s %s" % (entry.category, entry.full_name))
        if PENDING_NAMESPACES:
            self.stdout.write("\napps aún sin catalogar (no cuentan como huérfanas):")
            for namespace, motive in sorted(PENDING_NAMESPACES.items()):
                self.stdout.write("  %-16s %s" % (namespace or "(sin namespace)", motive))

    def _print_untested(self, features, entries):
        untested = fc.untested_features(features, entries)
        self.stdout.write("%d de %d funcionalidades sin ninguna prueba\n"
                          % (len(untested), len(features)))
        for feature in untested:
            self.stdout.write("  %-8s %s" % (feature.id, feature.name))

    def _print_roles(self, features):
        never = {role.id for role in fc.roles_never_exercised(features)}
        self.stdout.write("Eje de roles: %d canónicos, %d pseudo-roles\n"
                          % (len(CANONICAL_ROLES), len(PSEUDO_ROLES)))
        for role in CANONICAL_ROLES:
            mark = "—" if role.id in never else "sí"
            self.stdout.write("  %-3s %-34s %s" % (mark, role.name, role.defined_in))
        self.stdout.write("\n%d roles canónicos no aparecen en ningún paso del catálogo."
                          % len(never))

    # -- salidas -----------------------------------------------------------

    def _render_summary(self, features, entries):
        by_name = {e.full_name: e for e in entries}
        lines = ["%d funcionalidades catalogadas" % len(features), ""]
        for feature in features:
            touched, complete, selenium = fc.coverage(feature, by_name)
            estado = "completa" if complete else ("parcial" if touched else "sin prueba")
            lines.append("  %-8s %-58s %-10s %s"
                         % (feature.id, feature.name[:58], estado,
                            "selenium" if selenium else ""))
        orphans = fc.orphan_routes(entries, features)
        never = fc.roles_never_exercised(features)
        lines += [
            "",
            "  rutas huérfanas: %d" % len(orphans),
            "  roles canónicos sin aparecer en el catálogo: %d de %d"
            % (len(never), len(CANONICAL_ROLES)),
            "  apps pendientes de catalogar: %d" % len(PENDING_NAMESPACES),
        ]
        return "\n".join(lines) + "\n"

    def _render_markdown(self, features, entries):
        by_name = {e.full_name: e for e in entries}
        out = io.StringIO()
        w = out.write

        w("# Inventario de funcionalidades\n\n")
        w("Generado por `make feature-catalog`. No editar a mano: se regenera.\n\n")
        w("Una **funcionalidad** es una acción de usuario de varios pasos, no una ruta.\n")
        w("Cada paso declara **qué rol lo ejecuta**, que es lo único de este catálogo\n")
        w("que no se puede deducir del código — y justamente lo que hacía falta para\n")
        w("poder decir qué roles no están probados.\n\n")
        w("La columna de cobertura sale de `annotate_coverage()` y es **una pista, no\n")
        w("una medición**: dice que alguna prueba nombra esa ruta, no que la ejercite\n")
        w("con ese rol.\n\n")

        w("## Resumen\n\n")
        untested = fc.untested_features(features, entries)
        orphans = fc.orphan_routes(entries, features)
        never = fc.roles_never_exercised(features)
        w("| Métrica | Valor |\n|---|---:|\n")
        w("| Funcionalidades catalogadas | %d |\n" % len(features))
        w("| Sin ninguna prueba | %d |\n" % len(untested))
        w("| Rutas navegables huérfanas | %d |\n" % len(orphans))
        w("| Apps pendientes de catalogar | %d |\n" % len(PENDING_NAMESPACES))
        w("| Roles canónicos | %d |\n" % len(CANONICAL_ROLES))
        w("| Roles canónicos sin aparecer en ningún paso | %d |\n\n" % len(never))

        w("## Funcionalidades\n\n")
        for feature in features:
            touched, complete, selenium = fc.coverage(feature, by_name)
            estado = "completa" if complete else ("parcial" if touched else "**sin prueba**")
            w("### `%s` — %s\n\n" % (feature.id, feature.name))
            w("*%s · %s · prioridad %s · cobertura por ruta: %s · Selenium: %s*\n\n"
              % (feature.module, feature.kind, feature.priority, estado,
                 "sí" if selenium else "—"))
            w("%s\n\n" % feature.description)
            if feature.states:
                w("Estados que atraviesa:\n\n")
                for state in feature.states:
                    w("- `%s`\n" % state)
                w("\n")
            w("| Paso | Actores | Permiso | Transición | Rutas |\n")
            w("|---|---|---|---|---|\n")
            for step in feature.steps:
                # Los conjuntos de actores se componen (SOLICITANTES + APROBADORES) y
                # a veces se solapan; sin deduplicar, el rol sale dos veces en la tabla.
                actores = ", ".join(
                    get_role(a).name for a in dict.fromkeys(step.actors)
                ) or "—"
                permisos = "<br>".join("`%s`" % p for p in step.permissions) or "—"
                rutas = "<br>".join("`%s`" % r for r in step.routes) or "—"
                w("| **%s** | %s | %s | %s | %s |\n"
                  % (step.name, actores, permisos, step.transition or "—", rutas))
            w("\n")
            if feature.notes:
                w("Hallazgos:\n\n")
                for note in feature.notes:
                    w("- %s\n" % note)
                w("\n")

        w("## Roles y quién los ejercita\n\n")
        never_ids = {role.id for role in never}
        w("| Rol | En el catálogo | Definido en |\n|---|:-:|---|\n")
        for role in CANONICAL_ROLES:
            w("| %s | %s | `%s` |\n"
              % (role.name, "—" if role.id in never_ids else "sí", role.defined_in))
        w("\nLos pseudo-roles no conceden permisos y se listan aparte:\n\n")
        w("| Actor | Capa | Cuenta como cobertura |\n|---|---|:-:|\n")
        for role in PSEUDO_ROLES:
            w("| %s | `%s` | %s |\n"
              % (role.name, role.layer, "sí" if role.counts_as_coverage else "**no**"))
        w("\n")

        if orphans:
            w("## Rutas navegables sin funcionalidad\n\n")
            for entry in orphans:
                w("- `%s` (%s)\n" % (entry.full_name, entry.category))
            w("\n")

        w("## Apps pendientes de catalogar\n\n")
        w("| App | Motivo |\n|---|---|\n")
        for namespace, motive in sorted(PENDING_NAMESPACES.items()):
            w("| `%s` | %s |\n" % (namespace or "(sin namespace)", motive))
        w("\n")

        w("## Excepciones\n\n")
        w("Rutas navegables que a propósito no pertenecen a ninguna funcionalidad.\n\n")
        w("| Ruta | Motivo |\n|---|---|\n")
        for name, motive in sorted(CATALOG_EXCLUDES.items()):
            w("| `%s` | %s |\n" % (name, motive))
        w("\n")
        return out.getvalue()
