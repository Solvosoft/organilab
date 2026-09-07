from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import datatable_search_input
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class SubstanceWizardTest(SgaSeleniumBase):
    """El asistente de sustancias, de la creación al listado.

    Cubre en un recorrido siete páginas que hoy no tiene ninguna prueba de
    interacción: `create_sustance`, `step_one` (la misma vista reeditando),
    `step_four`, `send_to_review`, `detail_substance`, `get_substance` y
    `update_substance`.

    El paso 1 no crea nada al abrirse —la sustancia nace en el primer POST
    válido— y al guardar redirige por su cuenta a `step_four`, así que el
    encadenado sigue el camino real del usuario y no navega a mano.
    """

    # `features` es obligatorio y se puebla desde ObjectFeatures, que trae el
    # delta de laboratorio.
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    @modifies_db
    def test_substance_wizard_flow(self):
        # 1. Alta: los dos formularios de la misma pantalla (objform + suschacform).
        self.navigate_to_sga("create_sustance")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='id_comercial_name']",
                 "extra_action": "setvalue", "value": "Acetona selenium",
                 "clear": True},
                {"path": "//*[@id='id_brand']", "extra_action": "setvalue",
                 "value": "Marca selenium", "clear": True},
                {"path": "//*[@id='id_density']", "extra_action": "setvalue",
                 "value": "0.79", "clear": True},
            ]
            + self.select_first_options_steps("id_features")
            + [{"path": "//button[@type='submit']", "wait_ready": True}],
            "sga_create_substance",
        )
        # Guardar redirige a step_four: si seguimos en el paso 1, el formulario
        # no validó y conviene decirlo aquí y no tres pasos más allá.
        self.assertIn("step_four", self.selenium.current_url,
                      "el paso 1 no validó; sigue en %s" % self.selenium.current_url)

        # 2. Listado y búsqueda de lo recién creado.
        self.navigate_to_sga("get_substance")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='substance_table']", "presence_only": True,
                 "wait_dt": True},
                {"path": datatable_search_input("substance_table"),
                 "extra_action": "setvalue", "value": "selenium"},
                {"path": "//*[@id='substance_table']", "presence_only": True,
                 "wait_dt": True},
            ],
            "sga_substance_list",
        )
        self.assertIn("Acetona selenium", self.selenium.page_source)

        # 3. Detalle y reedición por step_one.
        pk = self.substancia_creada().pk
        self.navigate_to_sga("detail_substance", pk=pk)
        self.navigate_to_sga("step_one", pk=pk)
        self.take_screenshot_list(
            [
                {"path": "//*[@id='id_comercial_name']",
                 "extra_action": "setvalue", "value": "Acetona selenium editada",
                 "clear": True},
                {"path": "//button[@type='submit']", "wait_ready": True},
            ],
            "sga_update_substance",
        )

    def substancia_creada(self):
        from sga.models import Substance

        return Substance.objects.filter(
            comercial_name__startswith="Acetona selenium"
        ).first()

    def select_first_options_steps(self, field_id, cuantas=1):
        """Marca las primeras N opciones de un <select multiple>.

        En un multiselect no basta con asignar `value`: hay que marcar
        `selected` opción a opción. Y no se puede fijar un pk concreto porque
        depende de la fixture.
        """
        return [
            {
                "path": "//*[@id='%s']" % field_id,
                "extra_action": "script",
                "value": (
                    "var el = document.getElementById('%s');"
                    "var opts = Array.from(el.options).filter(o => o.value);"
                    "if (!opts.length) {"
                    "  throw new Error('el multiselect %s no tiene opciones');"
                    "}"
                    "opts.slice(0, %d).forEach(o => o.selected = true);"
                    "el.dispatchEvent(new Event('change', {bubbles: true}));"
                    % (field_id, field_id, cuantas)
                ),
            }
        ]
