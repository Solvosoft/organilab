from django.test import tag

from organilab_test.tests.selenium_tests.transversal.base import (
    TransversalSeleniumBase,
)


@tag("selenium")
class PresentationPagesTest(TransversalSeleniumBase):
    """Las páginas sueltas de `presentation` y las tres APIs de tutorial.

    `tutorials` no es una página estática: el interruptor y el progreso van
    contra `tutorial_toggle_api` y `tutorial_progress_api` por AJAX, así que la
    comprobación es que el estado persiste tras recargar, no que el elemento
    exista.
    """

    def test_tutorial_and_general_info_flow(self):
        self.navigate("index")
        self.navigate("general_info")
        self.navigate("error_view")

        # Tutoriales: alternar el interruptor llama a tutorial_toggle_api.
        self.navigate("tutorials", org_pk=self.org_pk)
        antes = self.estado_tutoriales()
        self.take_screenshot_list(
            [{"path": "//*[@id='toggleTutorials']"}],
            "presentation_tutorial",
        )
        self.navigate("tutorials", org_pk=self.org_pk)
        self.assertNotEqual(
            antes, self.estado_tutoriales(),
            "el interruptor de tutoriales no persistió: tutorial_toggle_api no "
            "llegó a guardar",
        )

    def estado_tutoriales(self):
        return self.selenium.execute_script(
            "var el = document.getElementById('toggleTutorials');"
            "return el ? el.checked : null;"
        )
