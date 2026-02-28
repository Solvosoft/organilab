from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap4ProceduresTest(CapacitacionSeleniumBase):
    """Capitulo 4: Procedimientos de laboratorio."""

    def test_create_procedure(self):
        """Escenario 4.1: Crear un procedimiento."""
        self.navigate_to_procedure_create(org_pk=4)

        path_list = [
            # Campo titulo del procedimiento
            {
                "path": ".//input[@id='id_title']",
                "extra_action": "setvalue",
                "value": "Analisis de pH en Muestras de Agua",
            },
            # Campo descripcion (TinyMCE si esta disponible, textarea como fallback)
            {
                "path": ".//form[1]",
                "extra_action": "script",
                "value": (
                    'if(typeof tinymce !== "undefined" && tinymce.get("id_description"))'
                    '{tinymce.get("id_description").setContent('
                    '"<p>Procedimiento estandar para la medicion de pH '
                    'en muestras de agua potable y residual.</p>");}'
                ),
                "sleep": 1,
            },
            # Guardar procedimiento
            {
                "path": ".//button[@type='submit' and contains(@class,'btn-success')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
        ]
        self.create_gif_process(path_list, "cap4_create_procedure")

    def test_view_procedure_list(self):
        """Escenario 4.2: Ver listado de procedimientos."""
        self.navigate_to_procedure_list(org_pk=4)

        path_list = [
            # Esperar a que cargue el DataTable de procedimientos
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap4_procedure_list",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap4_view_procedure_list")

    def test_view_my_procedures(self):
        """Escenario 4.3: Ver mis procedimientos."""
        # Login como docente
        self.login_as(user_pk=4)
        self.navigate_to_my_procedures(org_pk=4, lab_pk=1)

        path_list = [
            # Esperar a que cargue la pagina de mis procedimientos
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap4_my_procedures",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap4_view_my_procedures")
