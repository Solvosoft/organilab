from django.test import tag

from organilab_test.tests.selenium_xpaths import (
    REPORT_MODAL_DOWNLOAD,
    datatable_search_input,
)
from report.tests.selenium_tests.base import ReportSeleniumBase


@tag("selenium")
class RegencyReportTest(ReportSeleniumBase):
    """Reporte de regencia: plantilla propia y rutas de organización.

    `regency_report.html` repite los ids del formulario común (#send,
    #textstatus, #reportModal...), así que reutiliza los mismos pasos, pero por
    debajo va contra `create_organization_report_request` /
    `generate_organization_report` / `report_organization_status`, que son otras
    tres rutas. De ahí que merezca su propio flujo en vez de sumarse al lote.
    """

    def test_regency_report_flow(self):
        self.navigate_to_report("regency_report")
        self.take_screenshot_list(
            self.fill_report_form_steps(
                name="rep-regencia", title="Reporte de regencia", fmt="xlsx"
            )
            + self.send_report_steps()
            + [{"path": REPORT_MODAL_DOWNLOAD, "presence_only": True}],
            "report_regency",
        )
        self.assert_no_report_error()


@tag("selenium")
class PrecursorReportTest(ReportSeleniumBase):
    """Reporte de precursores y su tabla de valores.

    Tiene plantilla propia (`precursor_report.html`, tabla `#logtable`) y una
    segunda pantalla, `precursor_report_values_view`, que sí es un CRUD
    gentelella estándar.
    """

    def test_precursor_report_flow(self):
        self.navigate_to_report("precursor_report")
        self.take_screenshot_list(
            [{"path": "//*[@id='logtable']", "presence_only": True,
              "wait_dt": True},
             {"path": datatable_search_input("logtable"),
              "extra_action": "setvalue", "value": "a"},
             {"path": "//*[@id='logtable']", "presence_only": True,
              "wait_dt": True}],
            "report_precursor",
        )
