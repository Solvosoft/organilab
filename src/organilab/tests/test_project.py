"""Piezas del paquete de proyecto que alcanza una petición web."""
import importlib

from django.test import TestCase, override_settings
from django.urls import clear_url_caches, resolve

import organilab
from organilab import urls as project_urls


class CheckOkTest(TestCase):
    """`check_ok/` es la sonda de vida; con `?fail=` provoca un error a propósito
    para comprobar que el reporte de errores (Sentry/Glitchtip) llega."""

    def test_responde_ok(self):
        response = self.client.get("/check_ok/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_fail_lanza_la_excepcion(self):
        with self.assertRaises(ZeroDivisionError):
            self.client.get("/check_ok/", {"fail": "1"})


class VersionTest(TestCase):
    def test_get_version(self):
        self.assertEqual(organilab.get_version(), organilab.__version__)


class DebugUrlsTest(TestCase):
    """Con DEBUG los medios y el catálogo JS se sirven sin pasar por `media_access`."""

    def tearDown(self):
        importlib.reload(project_urls)
        clear_url_caches()

    def test_rutas_de_desarrollo(self):
        with override_settings(DEBUG=True):
            importlib.reload(project_urls)
            names = {getattr(p, "name", None) for p in project_urls.urlpatterns}
        self.assertIn("javascript-catalog", names)
        self.assertNotIn("media", names)
        clear_url_caches()
        importlib.reload(project_urls)
        self.assertEqual(resolve("/media/x.pdf").url_name, "media")
