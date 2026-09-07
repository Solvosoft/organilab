from django.test import tag

from organilab_test.tests.selenium_xpaths import (
    REPORT_MODAL_DOWNLOAD,
    datatable_search_input,
)
from report.tests.selenium_tests.base import ReportSeleniumBase


@tag("selenium")
class ReportAsyncCycleTest(ReportSeleniumBase):
    """El ciclo asíncrono de reportes, de principio a fin.

    Este único flujo representa a las ONCE vistas que comparten
    `report/base_report_form_view.html` (ObjectList, LimitedShelfObjectList,
    ReactivePrecursorObjectList, LogObjectView, DiscardShelfReportView,
    ReactiveReport, RiskZoneReport, ReactiveStockReport, FurnitureReportView,
    CompatibilityReport, HazardMapReport y DonationReportView): es la misma
    pantalla con otro dataset. Lo que las diferencia —cada formulario y cada
    constructor de dataset— se cubre recorriendo `report/register.py` con
    pruebas unitarias, no repitiendo este flujo once veces.

    Lo que justifica Selenium es justo lo que `client.get()` no puede ver: el
    botón dispara una petición, se pinta un panel de estado, y al final aparece
    la descarga. Y son DOS finales distintos, así que el flujo recorre los dos:
    un formato de fichero termina en el modal de descarga, y `html` abre el
    reporte en una pestaña nueva (`report_table`).
    """

    def test_report_async_cycle_flow(self):
        # 1. El índice de reportes, de donde parte el usuario.
        self.navigate_to_reports_index()

        # 2. Rama de fichero: el ciclo termina en el modal con el enlace.
        self.navigate_to_report("reports_objects_list")
        self.take_screenshot_list(
            self.fill_report_form_steps(
                name="reporte-objetos-selenium",
                title="Reporte de objetos",
                fmt="xlsx",
            )
            + self.send_report_steps()
            + [{"path": REPORT_MODAL_DOWNLOAD, "presence_only": True}],
            "report_async_cycle",
        )
        self.assert_no_report_error()

        # 3. Rama en pantalla: el mismo formulario en html salta a report_table.
        self.navigate_to_report("reports_objects_list")
        self.take_screenshot_list(
            self.fill_report_form_steps(
                name="reporte-objetos-pantalla",
                title="Reporte de objetos en pantalla",
                fmt="html",
            )
            + [{"path": "//*[@id='send']"}],
            "report_async_cycle",
        )

        original = self.switch_to_new_tab()
        try:
            self.take_screenshot_list(
                [
                    {"path": "//*[@id='table_id']", "presence_only": True,
                     "wait_dt": True},
                    {"path": datatable_search_input("table_id"),
                     "extra_action": "setvalue", "value": "a"},
                    {"path": "//*[@id='table_id']", "presence_only": True,
                     "wait_dt": True},
                ],
                "report_table",
            )
        finally:
            # El navegador se reutiliza entre tests: una pestaña huérfana
            # confunde a los flujos que buscan por window.name.
            self.close_extra_windows()
            self.selenium.switch_to.window(original)
