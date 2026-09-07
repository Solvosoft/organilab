from django.test import tag

from organilab_test.tests.selenium_xpaths import REPORT_MODAL_DOWNLOAD
from report.tests.selenium_tests.base import ReportSeleniumBase


@tag("selenium")
class OrgAndLabReportsTest(ReportSeleniumBase):
    """Las vistas que comparten `base_report_form_view.html` sin nada propio.

    Todas son la misma pantalla con otro dataset y el mismo formulario mínimo
    (nombre y título; `organization` y `report_name` van ocultos con initial, y
    `laboratory` es opcional). Se recorren en un solo test porque lo que se
    comprueba es que cada una arranca su ciclo y llega a la descarga, no que el
    formulario funcione seis veces.

    El formato se elige por reporte a propósito: no todos ofrecen los cinco.
    """

    # (namespace, urlname, formato, ¿lleva lab_pk?)
    REPORTES = (
        ("report", "reactive_precursor_object_list", "xlsx", False),
        ("report", "reactive_report", "xlsx", False),
        ("report", "donations_report", "xlsx", False),
        ("laboratory", "organizationreactivepresence", "xlsx", False),
        ("laboratory", "chemicalinventory", "xlsx", False),
        ("laboratory", "reports_laboratory", "xlsx", True),
    )

    def test_org_and_lab_reports_flow(self):
        for namespace, urlname, fmt, con_lab in self.REPORTES:
            with self.subTest(reporte=urlname):
                kwargs = {"org_pk": self.org_pk}
                if con_lab:
                    kwargs["lab_pk"] = self.lab_pk
                self.navigate(urlname, namespace=namespace, **kwargs)
                self.take_screenshot_list(
                    self.fill_report_form_steps(
                        name="rep-%s" % urlname.replace("_", "-"),
                        title="Reporte %s" % urlname,
                        fmt=fmt,
                    )
                    + self.send_report_steps()
                    + [{"path": REPORT_MODAL_DOWNLOAD, "presence_only": True}],
                    "report_%s" % urlname,
                )
                self.assert_no_report_error()
