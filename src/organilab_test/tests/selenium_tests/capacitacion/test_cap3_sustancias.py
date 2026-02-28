from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap3SubstancesTest(CapacitacionSeleniumBase):
    """Capitulo 3: Gestion de sustancias y Sistema Globalmente Armonizado (SGA)."""

    def test_create_substance(self):
        """Escenario 3.1: Crear una sustancia (Paso 1 - Datos basicos)."""
        self.navigate_to_sga_create_substance(org_pk=4)

        path_list = [
            # Establecer nombre comercial via JS (widget djgentelella no permite send_keys)
            {
                "path": ".//input[@id='id_comercial_name']",
                "extra_action": "script",
                "value": "document.getElementById('id_comercial_name').value = 'Acido Sulfurico Concentrado';",
                "wait_ready": True,
                "scroll": "window.scrollTo(0, 0)",
            },
            # Establecer nombre IUPAC
            {
                "path": ".//input[@id='id_uipa_name']",
                "extra_action": "script",
                "value": "document.getElementById('id_uipa_name').value = 'Sulfuric Acid';",
            },
            # Establecer descripcion
            {
                "path": ".//textarea[@id='id_description']",
                "extra_action": "script",
                "value": "document.getElementById('id_description').value = "
                "'Acido sulfurico concentrado al 98% para uso analitico';",
                "scroll": "window.scrollTo(0, 400)",
            },
            # Guardar / Continuar
            {
                "path": ".//button[@type='submit' and contains(@class,'btn-success')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
        ]
        self.create_gif_process(path_list, "cap3_create_substance", hover=False)

    def test_view_sga_label(self):
        """Escenario 3.2: Ver formulario de etiqueta SGA."""
        self.navigate_to_sga_label_create(org_pk=4)

        path_list = [
            # Capturar vista del formulario de etiqueta SGA
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_sga_label_form",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_view_sga_label")

    def test_view_msds(self):
        """Escenario 3.3: Ver listado de hojas de seguridad (MSDS)."""
        self.navigate_to_msds(org_pk=4)

        path_list = [
            # Capturar vista del indice MSDS
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_msds_list",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_view_msds")
