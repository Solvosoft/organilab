from django.test import tag
from django.utils import timezone

from organilab_test.tests.base import modifies_db
from risk_management.tests.selenium_tests.iper.base import IperSeleniumBase


@tag("selenium")
class IperAssessmentFlowTest(IperSeleniumBase):
    """Listado, detalle y alta de un peligro de una evaluación IPER.

    Este flujo es además la prueba de que el re-sembrado de
    `IperSeleniumBase._fixture_setup` funciona: los desplegables de
    probabilidad y consecuencia del formulario de peligro se pueblan desde
    `Catalog`, y `Catalog` lo siembra la migración `0033_seed_iper`, que el
    flush de `TransactionTestCase` se lleva por delante. Si el re-sembrado
    fallara, esos selects saldrían vacíos y el paso lo diría con todas las
    letras en vez de fallar con un "no encontré el elemento".

    La evaluación de partida se crea por ORM a propósito. El alta por pantalla
    (`iper_create`) usa el autocomplete `labs_by_org`, un select2 por AJAX cuyo
    queryset depende del perfil del usuario además de la organización
    (`report/gtselects.py:144`), y montar ese escenario es un flujo aparte —el
    del formulario de alta— que no tiene por qué bloquear la cobertura del
    detalle, que es donde vive la lógica de IPER.
    """

    def setUp(self):
        super().setUp()
        self.assessment = self.crear_evaluacion()

    def crear_evaluacion(self):
        from laboratory.models import Laboratory, OrganizationStructure
        from risk_management.models import IPERAssessment

        lab = Laboratory.objects.filter(organization_id=self.org_pk).first()
        return IPERAssessment.objects.create(
            organization=OrganizationStructure.objects.get(pk=self.org_pk),
            laboratory=lab,
            created_by=self.user,
            responsible=self.user,
            assessment_date=timezone.localdate(),
            version=1,
        )

    @modifies_db
    def test_iper_assessment_flow(self):
        # 1. Listado: la tabla carga y trae la evaluación.
        self.navigate_to_iper("iper_list")
        self.take_screenshot_list(
            [{"path": "//*[@id='table-iper']", "presence_only": True,
              "wait_dt": True}],
            "iper_assessment",
        )

        # 2. Detalle: matriz de riesgo y alta de un peligro.
        self.navigate_to_iper("iper_detail", pk=self.assessment.pk)
        self.take_screenshot_list(
            [{"path": "//*[@id='risk-matrix-table']", "presence_only": True}]
            + self.select_first_option_steps("id_category")
            + [
                {"path": "//*[@id='id_description']", "extra_action": "setvalue",
                 "value": "Peligro selenium", "clear": True},
                {"path": "//*[@id='id_location']", "extra_action": "setvalue",
                 "value": "Bodega", "clear": True},
            ]
            + self.select_first_option_steps("id_probability")
            + self.select_first_option_steps("id_consequence")
            + [{"path": "//form[contains(@action, 'hazard/create')]"
                        "//button[@type='submit']"}],
            "iper_assessment",
        )
        self.assertIn("Peligro selenium", self.selenium.page_source)

    def select_first_option_steps(self, field_id, index=1):
        """Elige la opción N de un <select> poblado desde la base de datos.

        No se puede fijar un `value` concreto: los pk de `Catalog` los asigna la
        semilla y cambian entre corridas. Se toma la primera opción real,
        saltando el "---------" vacío, y si no hay ninguna se falla con un
        mensaje que apunta a la causa probable.
        """
        return [
            {
                "path": "//*[@id='%s']" % field_id,
                "extra_action": "script",
                "value": (
                    "var el = document.getElementById('%s');"
                    "var opts = Array.from(el.options).filter(o => o.value);"
                    "if (!opts.length) {"
                    "  throw new Error('el select %s no tiene opciones:"
                    " probablemente no se sembro Catalog tras el flush');"
                    "}"
                    "el.value = opts[%d].value;"
                    "el.dispatchEvent(new Event('change', {bubbles: true}));"
                    % (field_id, field_id, index - 1)
                ),
            }
        ]
