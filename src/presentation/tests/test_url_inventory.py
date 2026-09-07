# encoding: utf-8
"""Guardianes del inventario de rutas.

Un inventario que se pudre es peor que no tenerlo: `URLNAME_PERMISSIONS` ya
enseñó cómo termina eso. Estas pruebas son lo que mantiene el fichero honesto.
"""

from django.core.management import call_command
from django.test import TestCase

from presentation.url_inventory import build_inventory, counts_by_category


class UrlInventoryTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.entries = build_inventory()

    def test_ninguna_ruta_queda_sin_clasificar(self):
        """`desconocida` existe para obligar a decidir, no para acumular casos.

        Si una ruta nueva cae aquí: o se arregla la cascada de `classify()`, o se
        añade a `OVERRIDES` con el motivo escrito.
        """
        unknown = [e.full_name for e in self.entries if e.category == "desconocida"]
        self.assertEqual([], unknown, "rutas sin clasificar: %s" % ", ".join(unknown))

    def test_el_inventario_commiteado_esta_al_dia(self):
        """Los dos ficheros generados deben reflejar el código de hoy.

        El CSV entra aquí por una razón concreta: durante toda su vida se generó
        sin cobertura —`annotate_coverage()` estaba condicionada a `--coverage`,
        que el Makefile no pasaba— y sus columnas `selenium` y `pruebas` valían
        cero en las 1 681 filas. Nadie lo vio porque este guardián solo miraba el
        markdown. Un fichero generado que no se comprueba no está vivo.
        """
        from pathlib import Path

        from django.conf import settings

        roadmap = Path(settings.BASE_DIR).parent / "roadmap"
        for name in ("INVENTARIO_URLS.md", "inventario_urls.csv"):
            path = roadmap / name
            with self.subTest(fichero=name):
                if not path.exists():
                    self.skipTest("todavía no se generó %s" % name)
                try:
                    call_command("url_inventory", check=str(path), verbosity=0)
                except Exception as exc:  # noqa: BLE001
                    self.fail("%s\nRegeneralo con `make url-inventory`." % exc)

    def test_no_se_pierden_paginas(self):
        """Umbral de regresión: nadie convierte páginas en endpoints sin querer."""
        counts = counts_by_category(self.entries)
        self.assertGreaterEqual(
            counts["pagina"], 165,
            "el clasificador ve %d páginas; eran 172. ¿Se rompió una heurística?"
            % counts["pagina"],
        )

    def test_los_nombres_duplicados_son_los_conocidos(self):
        """Un nombre repetido deja una ruta muerta: `reverse` solo devuelve una.

        La lista blanca son duplicados auditados y benignos. Cualquier otro es un
        hallazgo que hay que mirar.
        """
        conocidos = {
            # Dos firmas de la misma vista, con y sin <int:user>.
            "laboratory:create_user_qr",
        }
        found = {e.full_name for e in self.entries if e.duplicated}
        self.assertEqual(
            set(), found - conocidos,
            "nombres duplicados nuevos: %s" % ", ".join(sorted(found - conocidos)),
        )
