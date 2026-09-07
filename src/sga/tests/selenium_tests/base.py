from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase


class SgaSeleniumBase(OptimizedSeleniumBase):
    """Base de las suites Selenium de la app `sga`.

    Hereda de OptimizedSeleniumBase para que `@modifies_db` surta efecto: los
    flujos de SGA crean sustancias, etiquetas y filas de catálogo, así que casi
    todos ensucian y conviene pagar el flush solo donde toca.

    La navegación va por `reverse()` y no por el menú lateral.
    """

    # Solo el esquema base. Los flujos que necesiten catálogos GHS,
    # sustancias o plantillas precargadas añaden su propio delta: no se
    # carga de más para todos, y cada delta se justifica donde se usa.
    fixtures = ["selenium/base_selenium.json"]

    org_pk = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Las páginas de SGA no cargan jQuery: el cursor de las capturas se
        # pinta con JS nativo, igual que en CapacitacionSeleniumBase.
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

    def navigate(self, urlname, namespace="sga", **kwargs):
        params = kwargs.pop("_query", None)
        url = self.live_server_url + str(
            reverse("%s:%s" % (namespace, urlname), kwargs=kwargs)
        )
        if params:
            url = "%s?%s" % (url, urlencode(params))
        self.open_url(url)
        self.wait_for_page_ready()

    def navigate_to_sga(self, urlname, **kwargs):
        kwargs.setdefault("org_pk", self.org_pk)
        self.navigate(urlname, **kwargs)
