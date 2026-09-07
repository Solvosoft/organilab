from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase


class ManageLaboratorySeleniumBase(OptimizedSeleniumBase):
    """Base compartida de los flujos de gestión de laboratorio.

    Las suites de esta carpeta declaraban su propia clase base en cada fichero
    (ObjectSeleniumBase, LaboratorySeleniumBase, ...), cada una con su lista de
    `navigate_to_*`. Los flujos nuevos usan esta, con un `navigate()` genérico
    por nombre de ruta, para no seguir multiplicando métodos de un solo uso.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    org_pk = 1
    lab_pk = 1

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate(self, urlname, namespace="laboratory", **kwargs):
        params = kwargs.pop("_query", None)
        url = self.live_server_url + str(
            reverse("%s:%s" % (namespace, urlname), kwargs=kwargs)
        )
        if params:
            url = "%s?%s" % (url, urlencode(params))
        self.open_url(url)
        self.wait_for_page_ready()

    def navigate_to_lab(self, urlname, **kwargs):
        """Ruta con los dos kwargs que lleva casi todo el módulo."""
        kwargs.setdefault("org_pk", self.org_pk)
        kwargs.setdefault("lab_pk", self.lab_pk)
        self.navigate(urlname, **kwargs)
