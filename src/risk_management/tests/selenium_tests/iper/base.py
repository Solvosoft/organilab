from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase


class IperSeleniumBase(OptimizedSeleniumBase):
    """Base de la suite Selenium del módulo IPER.

    El detalle que hace falta entender aquí: los catálogos de IPER (las cuatro
    claves de `Catalog`, las 9 filas de `IPERRiskMatrix` y una `IPERConfig` por
    organización raíz) los siembra la migración
    `risk_management/migrations/0033_seed_iper.py`. Pero estas pruebas son
    `TransactionTestCase`, que hace **flush** de la base entre tests y se lleva
    por delante todo lo sembrado por migraciones —es exactamente el problema que
    dejó sin `BaseUnitValues` a la fixture `laboratory_view.json`—. Sin esos
    catálogos, IPER no puede calcular un solo nivel de riesgo.

    En vez de congelar las filas en un delta —que se desincronizaría en cuanto
    cambiara la semilla— se vuelve a invocar `seed_iper()`, que es la misma
    función que usa la migración y acepta las clases de modelo. Así los datos de
    prueba y los de producción no pueden divergir.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/risk_delta.json"]

    org_pk = 1

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.seed_iper_catalogs()

    @staticmethod
    def seed_iper_catalogs():
        from laboratory.models import Catalog, OrganizationStructure
        from risk_management.iper_defaults import seed_iper
        from risk_management.models import IPERConfig, IPERRiskMatrix

        # seed_iper es idempotente (todo get_or_create), así que repetirlo tras
        # cada recarga de fixtures es inocuo.
        seed_iper(Catalog, IPERRiskMatrix, IPERConfig, OrganizationStructure)

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate(self, urlname, namespace="riskmanagement", **kwargs):
        params = kwargs.pop("_query", None)
        url = self.live_server_url + str(
            reverse("%s:%s" % (namespace, urlname), kwargs=kwargs)
        )
        if params:
            url = "%s?%s" % (url, urlencode(params))
        self.open_url(url)
        self.wait_for_page_ready()

    def navigate_to_iper(self, urlname, **kwargs):
        kwargs.setdefault("org_pk", self.org_pk)
        self.navigate(urlname, **kwargs)
