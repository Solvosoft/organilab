# encoding: utf-8
"""Base del smoke del labview nuevo.

Se navega con aserciones directas y no con listas de XPath para GIF: lo que hay
que demostrar aquí es que el mapa **hace** lo que promete —desplegar,
seleccionar, filtrar, editar—, no cómo se ve mientras lo hace.

Los selectores van por clase y por ``data-*``, nunca por XPath absoluto: los
absolutos ya murieron una vez con el layout de la 0.6.0 y volverían a morir con
el próximo retoque de plantilla.

Aviso: el usuario del fixture es **superusuario**, y ``ProfileMiddleware`` se
salta a los superusuarios (``authentication/middleware.py:50``).  Aquí no se
asevera nada sobre permisos; de eso se ocupa la matriz de la suite unit.
"""

from django.contrib.auth.models import User
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from organilab_test.tests.base import SeleniumBase


class LabviewSeleniumBase(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    org_pk = 1
    lab_pk = 1

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    # -- navegación --------------------------------------------------------

    def labview_url(self, query=""):
        path = reverse(
            "laboratory:labview",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab_pk},
        )
        return self.live_server_url + path + query

    def open_labview(self, query=""):
        self.selenium.get(self.labview_url(query))
        self.wait_for_tree()

    def wait_for_tree(self):
        self.wait_for(".labview-room")

    # -- espera ------------------------------------------------------------

    def wait_for(self, css):
        return WebDriverWait(self.selenium, self.element_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css)),
            message="no apareció %s en %s" % (css, self.selenium.current_url),
        )

    def wait_until(self, predicate, message):
        return WebDriverWait(self.selenium, self.element_timeout).until(
            lambda driver: predicate(), message=message
        )

    def find_all(self, css):
        return self.selenium.find_elements(By.CSS_SELECTOR, css)

    def find(self, css):
        return self.selenium.find_element(By.CSS_SELECTOR, css)

    def click(self, css):
        element = self.wait_for(css)
        self.selenium.execute_script("arguments[0].scrollIntoView(true);", element)
        self.selenium.execute_script("arguments[0].click();", element)
        return element

    # -- nodos del mapa ----------------------------------------------------

    def room_css(self, pk):
        return '.labview-room[data-room="%d"]' % pk

    def room_body_css(self, pk):
        return "%s .labview-room-body" % self.room_css(pk)

    def furniture_css(self, pk):
        return '.labview-furniture[data-furniture="%d"]' % pk

    def shelf_item_css(self, pk):
        return '[data-pg-item="%d"]' % pk

    def is_visible(self, css):
        elements = self.find_all(css)
        return bool(elements) and elements[0].is_displayed()
