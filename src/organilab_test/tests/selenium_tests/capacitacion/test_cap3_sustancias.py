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
            # Establecer marca comercial. El asistente ya no pide el nombre
            # IUPAC en el paso 1: SustanceObjectForm expone nombre, sinonimos,
            # caracteristicas, descripcion, marca y organizacion.
            {
                "path": ".//input[@id='id_brand']",
                "extra_action": "script",
                "value": "document.getElementById('id_brand').value = 'Merck';",
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


@tag("selenium")
class Cap3ClassificationAndMSDSTest(CapacitacionSeleniumBase):
    """Capitulo 3: Clasificacion SGA, MSDS y precursores."""

    def test_sga_classification_form(self):
        """Escenario 3.4: Ver formulario de clasificacion SGA con codigos H y P."""
        self.navigate_to_sga_update_substance(org_pk=4, pk=1)

        path_list = [
            # Capturar formulario de clasificacion SGA
            {
                "path": "//body",
                "wait_ready": True,
            },
            # Scroll para mostrar los codigos H y P
            {
                "path": "//body",
                "scroll": "window.scrollTo(0, 300)",
                "screenshot_name": "cap3_sga_classification",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_sga_classification")

    def test_upload_msds_form(self):
        """Escenario 3.5: Ver el campo para subir la hoja de seguridad.

        La ficha ya no se sube desde una pantalla propia de MSDS: forma parte
        del paso 1 del asistente de sustancias, en el campo de hoja de
        seguridad, que al subirla encola su lectura automatica.
        """
        self.navigate_to_sga_create_substance(org_pk=4)

        path_list = [
            # Capturar el formulario con el campo de la ficha de seguridad
            {
                "path": "//input[@id='id_security_sheet']",
                "wait_ready": True,
                "scroll": "document.getElementById('id_security_sheet')"
                ".scrollIntoView({block:'center'});",
                "screenshot_name": "cap3_msds_upload_form",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_msds_upload_form")

    def test_precursor_config_and_report(self):
        """Escenario 3.6: Ver configuracion de precursor y reporte mensual."""
        # Ver reporte de precursores
        self.navigate_to_precursor_report(org_pk=4)

        path_list = [
            # Capturar vista del reporte de precursores
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_precursor_report",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_precursor_report")

        # Ver configuracion de precursor en caracteristicas de sustancia
        self.navigate_to_sga_update_substance(org_pk=4, pk=1)

        path_list_config = [
            # Capturar la seccion de precursor en el formulario
            {
                "path": "//body",
                "wait_ready": True,
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
            {
                "path": "//body",
                "screenshot_name": "cap3_precursor_config",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_config, "cap3_precursor_config")
