from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase
from organilab_test.tests.selenium_xpaths import (
    REPORT_DOWNLOAD_LINK,
    REPORT_ERROR_BOX,
    REPORT_MODAL,
    REPORT_SEND_BTN,
    REPORT_STATUS_PANEL,
)


class ReportSeleniumBase(OptimizedSeleniumBase):
    """Base de las suites de la app `report`.

    Hereda de OptimizedSeleniumBase y no de SeleniumBase: sin ello `@modifies_db`
    es un no-op y cada test pagaría un flush más un loaddata completo. Los
    reportes no escriben en el dominio (solo crean un TaskReport), así que casi
    ningún test de esta suite necesita la marca.

    La navegación va siempre por `reverse()` y nunca por el menú lateral: el
    sidebar depende de los permisos del usuario y de la organización activa, y
    un cambio de menú no debería tumbar una prueba de reportes.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    org_pk = 1
    lab_pk = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Igual que CapacitacionSeleniumBase: no todas las páginas cargan jQuery,
        # así que el cursor de las capturas se pinta con JS nativo.
        cls.show_cursor_script = """
            if(!document.querySelector('.cursor_pointer')){
        """ + cls.cursor_script + """
            }
            var cursor = document.querySelector(".cursor_pointer");
            cursor.style.zIndex = '9999';
        """

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    # --- Navegación ---

    def navigate(self, urlname, namespace="report", **kwargs):
        """Abre una ruta por nombre y espera a que la página esté lista."""
        params = kwargs.pop("_query", None)
        url = self.live_server_url + str(
            reverse("%s:%s" % (namespace, urlname), kwargs=kwargs)
        )
        if params:
            url = "%s?%s" % (url, urlencode(params))
        self.open_url(url)
        self.wait_for_page_ready()

    def navigate_to_report(self, urlname, **kwargs):
        kwargs.setdefault("org_pk", self.org_pk)
        self.navigate(urlname, **kwargs)

    def navigate_to_reports_index(self):
        self.navigate("reports", namespace="laboratory", org_pk=self.org_pk)

    # --- Pasos reutilizables del ciclo de reporte ---

    def fill_report_form_steps(self, name, title, fmt="xlsx"):
        """Pasos para rellenar el formulario común de `base_report_form_view.html`.

        `organization` y `report_name` son campos ocultos que la vista ya trae
        rellenos por `initial`, y `laboratory` es opcional: si se deja vacío,
        `ReportForm.clean_laboratory` cae a todos los laboratorios de la
        organización. Por eso el mínimo viable son nombre, título y formato.
        """
        return [
            {"path": "//*[@id='id_name']", "extra_action": "setvalue",
             "value": name, "clear": True},
            {"path": "//*[@id='id_title']", "extra_action": "setvalue",
             "value": title, "clear": True},
        ] + self.select_option_steps("id_format", fmt)

    def send_report_steps(self):
        """Dispara #send y espera al final real del ciclo asíncrono.

        Con CELERY_ALWAYS_EAGER (organilab/test_settings.py) la tarea termina
        dentro del propio create_request, así que `get_doc` encuentra el fichero
        a la primera y no hay que aguantar los 5 s de polling de
        `get_archive_status`. Para un formato distinto de `html` el final
        observable es el modal de descarga; para `html` se abre otra pestaña.
        """
        return [
            {"path": REPORT_SEND_BTN},
            {"path": REPORT_STATUS_PANEL, "presence_only": True},
            {"path": REPORT_MODAL, "presence_only": True},
            {"path": REPORT_DOWNLOAD_LINK, "presence_only": True},
        ]

    def switch_to_new_tab(self):
        """Pasa a la pestaña recién abierta por `open_new_window()`.

        No se usa `change_focus_tab()` porque esa espera por `window.name`, y
        `general_reports.html` —la pantalla a la que salta el reporte en
        formato html— no lo fija; solo lo hacen las plantillas de formulario.
        """
        from selenium.webdriver.support.ui import WebDriverWait

        original = self.selenium.current_window_handle
        WebDriverWait(self.selenium, self.element_timeout).until(
            lambda d: len(d.window_handles) > 1,
            "el reporte en html no abrió ninguna pestaña nueva",
        )
        for handle in reversed(self.selenium.window_handles):
            if handle != original:
                self.selenium.switch_to.window(handle)
                break
        return original

    def assert_no_report_error(self):
        """El panel de error debe seguir oculto tras un envío correcto."""
        from selenium.webdriver.common.by import By

        boxes = self.selenium.find_elements(By.XPATH, REPORT_ERROR_BOX)
        for box in boxes:
            self.assertFalse(
                box.is_displayed(),
                "El reporte mostró un error: %s" % box.text,
            )
