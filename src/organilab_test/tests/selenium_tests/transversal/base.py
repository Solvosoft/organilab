from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase


class TransversalSeleniumBase(OptimizedSeleniumBase):
    """Base de los flujos que cruzan apps sin suite propia.

    Cubre las pantallas sueltas de `auth_and_perms`, `presentation`, `msds`,
    `derb` y `authentication`: cada una tiene una o tres páginas sin prueba, no
    dan para una suite por app, y comparten fixture.

    Nota: las reservas NO entran aquí. `capacitacion/test_cap5_reservaciones.py`
    ya cubre el flujo completo (listado, reservar, masiva, aprobar/rechazar,
    devolver y cerrar) y el inventario da `reservations_management: 2 páginas,
    0 sin prueba`.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    org_pk = 1
    lab_pk = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # No todas estas páginas cargan jQuery.
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

    def navigate(self, urlname, namespace=None, **kwargs):
        """Abre una ruta por nombre.

        `namespace` es opcional porque no todas las apps lo declaran:
        `presentation/urls.py` no define `app_name`, así que sus rutas viven en
        el espacio global y `reverse("presentation:index")` no resuelve.
        """
        params = kwargs.pop("_query", None)
        nombre = "%s:%s" % (namespace, urlname) if namespace else urlname
        url = self.live_server_url + str(reverse(nombre, kwargs=kwargs))
        if params:
            url = "%s?%s" % (url, urlencode(params))
        self.open_url(url)
        self.wait_for_page_ready()
