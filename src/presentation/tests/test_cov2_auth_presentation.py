"""Ramas de `presentation` que las pruebas por funcionalidad no alcanzaban."""

import os
import tempfile

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from presentation.pdf import link_callback_for


class LinkCallbackEstaticosTest(SimpleTestCase):
    """Un estático que los `finders` no encuentran se busca en `STATIC_ROOT`."""

    def test_estatico_recolectado_solo_en_static_root(self):
        with tempfile.TemporaryDirectory() as static_root:
            path = os.path.join(static_root, "solo-recolectado.css")
            open(path, "w").close()
            with override_settings(STATIC_ROOT=static_root, STATIC_URL="/static/"):
                callback = link_callback_for()
                self.assertEqual(callback("/static/solo-recolectado.css"), path)

    def test_estatico_inexistente_pasa_tal_cual(self):
        with tempfile.TemporaryDirectory() as static_root:
            with override_settings(STATIC_ROOT=static_root, STATIC_URL="/static/"):
                callback = link_callback_for()
                self.assertEqual(callback("/static/no-existe.css"), "/static/no-existe.css")

    def test_ruta_de_disco_suelta_pasa_tal_cual(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as archivo:
            self.assertEqual(link_callback_for()(archivo.name), archivo.name)


class VistaDeErrorTest(TestCase):
    def test_estado_no_numerico_cae_en_404(self):
        response = self.client.get(reverse("error_view"), {"status": "abc"})
        self.assertEqual(response.status_code, 404)

    def test_estado_conocido_se_respeta(self):
        response = self.client.get(reverse("error_view"), {"status": "403"})
        self.assertEqual(response.status_code, 403)
