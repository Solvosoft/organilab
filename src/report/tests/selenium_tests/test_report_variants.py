from django.test import tag

from organilab_test.tests.selenium_xpaths import (
    REPORT_FIELD_ERRORS,
    REPORT_MODAL_DOWNLOAD,
    select2_field,
    select2_result,
)
from report.tests.selenium_tests.base import ReportSeleniumBase


@tag("selenium")
class ReportFormVariantsTest(ReportSeleniumBase):
    """Lo que DIFERENCIA a los formularios de reporte, no lo que comparten.

    Lo compartido ya lo cubre `test_report_cycle` con un solo recorrido. Aquí
    van los casos que se salen del molde:

      - `object_change_logs` es el único que exige `laboratory` (el resto lo
        deja opcional y cae a todos los laboratorios de la organización).
      - `reactive_stock_report` solo ofrece ods y xlsx.
      - y el camino de error de cliente, que se pinta sin recargar la página.
    """

    def test_report_form_variants_flow(self):
        # 1. Reporte con laboratorio obligatorio: select2 acotado al campo.
        self.navigate_to_report("object_change_logs")
        self.take_screenshot_list(
            self.fill_report_form_steps(
                name="rep-cambios", title="Reporte de cambios", fmt="xlsx"
            )
            + [
                {"path": select2_field("id_laboratory")},
                {"path": select2_result(1)},
            ]
            + self.send_report_steps()
            + [{"path": REPORT_MODAL_DOWNLOAD, "presence_only": True}],
            "report_object_change_logs",
        )
        self.assert_no_report_error()

        # 2. Reporte con la lista de formatos recortada (solo ods y xlsx).
        self.navigate_to_report("reactive_stock_report")
        self.take_screenshot_list(
            self.fill_report_form_steps(
                name="rep-stock", title="Reporte de stock", fmt="ods"
            )
            + self.send_report_steps()
            + [{"path": REPORT_MODAL_DOWNLOAD, "presence_only": True}],
            "report_reactive_stock",
        )
        self.assert_no_report_error()

        # 3. Camino de error: sin nombre, el servidor devuelve form_errors y el
        #    JS los pinta junto al campo sin recargar. Es la rama de
        #    `form_field_errors()` en laboratory/js/reports.js.
        self.navigate_to_report("waste_report")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
                {"path": "//*[@id='send']"},
                {"path": REPORT_FIELD_ERRORS, "presence_only": True},
            ],
            "report_form_errors",
        )


@tag("selenium")
class ReportRiskViewsTest(ReportSeleniumBase):
    """Reportes con select2 múltiple y con pantalla propia de resultado."""

    def test_report_risk_compat_hazardmap_flow(self):
        for urlname, fmt in (
            ("risk_zone_report", "xlsx"),
            ("compatibility_report", "ods"),
            ("hazard_map_report", "pdf"),
        ):
            with self.subTest(reporte=urlname):
                self.navigate_to_report(urlname)
                self.take_screenshot_list(
                    self.fill_report_form_steps(
                        name="rep-%s" % urlname.replace("_", "-"),
                        title="Reporte %s" % urlname,
                        fmt=fmt,
                    )
                    + self.send_report_steps(),
                    "report_%s" % urlname,
                )
                self.assert_no_report_error()

        # El mapa de peligros tiene además su propia pantalla de visualización.
        self.navigate_to_report("hazard_map_visual")
