from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class LaboratoryViewSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )

        # Enlace "estructura del laboratorio" (rooms_list) del índice; el
        # XPath absoluto pre-0.6.0 murió con el layout nuevo.
        self.path_base = [
            {"path": "//a[contains(@href, '/rooms/') and not(contains(@href, 'create'))]"}
        ]

    def get_save_button_modal(self, id_modal):
        return "//*[@id='%s']/div/div/div[3]/button[2]" % id_modal

    def shelfobject_row_action(self, icon, row=1):
        """Acción por fila de la tabla de shelfobjects, por icono (estable
        ante reordenamientos de columnas/acciones; los td[N]/a[M] de DT1 no
        sobrevivieron a DataTables 2)."""
        return (
            "//table[@id='shelfobjecttable']//tbody/tr[%d]"
            "//a[.//i[contains(@class, '%s')]]" % (row, icon)
        )

    def shelfobject_toolbar_button(self, icon):
        """Botón del toolbar de la tabla de shelfobjects, por icono
        (fa-desktop equipo, fa-battery-quarter material, fa-flask reactivo,
        fa-cubes contenedores, fa-exchange transferencias)."""
        return (
            "//*[@id='shelfobjecttable_wrapper']"
            "//button[.//i[contains(@class, '%s')]]" % icon
        )

    def container_radio(self, form_id, value):
        """Radio de opciones de contenedor (inputs nativos gt-check desde
        djgentelella 0.6.0; antes eran <ins> de iCheck)."""
        return "//*[@id='%s']//input[@type='radio' and @value='%s']" % (
            form_id,
            value,
        )


@tag("selenium")
class LabViewTest(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def test_go_to_lab_view(self):
        path_list = [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[1]/a"
            },
        ]

        self.create_gif_process(path_list, "go_to_lab_view")
