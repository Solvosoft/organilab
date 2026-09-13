# encoding: utf-8
"""Recorrido completo del labview en un navegador de verdad.

Lo que la suite unit no puede demostrar: que el árbol se pinta, que pulsar una
celda trae la tabla del estante, que el overlay colorea, que un deep-link
aterriza donde dice y que el editor persiste por operación.

El fixture ``selenium/laboratory_view.json`` trae tres salas, cuatro muebles y
cinco estantes, con cuadrículas de una y dos celdas.
"""

from django.test import tag
from django.urls import reverse

from laboratory.models import Furniture, LaboratoryRoom, Shelf
from laboratory.tests.selenium_tests.labview_new.base import LabviewSeleniumBase


@tag("selenium")
class LabviewSmokeNavigationTest(LabviewSeleniumBase):

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.get(pk=1)
        self.furniture = self.shelf.furniture
        self.labroom = self.furniture.labroom

    # -- el recorrido ------------------------------------------------------

    def test_the_map_walks_room_furniture_shelf_and_table(self):
        self.open_labview()

        # La sala llega en el mapa, con su mueble y su estante dentro.
        self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
        self.wait_until(
            lambda: self.is_visible(self.furniture_css(self.furniture.pk)),
            "el mueble no apareció al desplegar la sala",
        )

        # Pulsar el estante trae su tabla, que empieza oculta.
        self.assertIn("d-none", self.find("#labview_table_wrapper")
                      .get_attribute("class"))
        self.click(self.shelf_item_css(self.shelf.pk))
        self.wait_until(
            lambda: "d-none" not in self.find("#labview_table_wrapper")
            .get_attribute("class"),
            "la tabla no se mostró al elegir el estante",
        )
        self.wait_for("#labview_shelfobjecttable tbody tr")

        # Y la URL conserva el estado, que es lo que hace copiable el enlace.
        self.assertIn("shelf=%d" % self.shelf.pk, self.selenium.current_url)

    def test_a_deep_link_lands_on_the_shelf_without_a_single_click(self):
        """El contrato de los QR impresos y del mapa de peligros."""
        self.open_labview(
            "?labroom=%d&furniture=%d&shelf=%d"
            % (self.labroom.pk, self.furniture.pk, self.shelf.pk)
        )
        self.wait_until(
            lambda: self.is_visible(self.room_body_css(self.labroom.pk)),
            "la sala del deep-link no llegó desplegada",
        )
        self.wait_until(
            lambda: "d-none" not in self.find("#labview_table_wrapper")
            .get_attribute("class"),
            "el deep-link no seleccionó el estante",
        )

    def test_the_risk_overlay_paints_and_unpaints(self):
        self.open_labview()
        self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
        self.wait_for(self.shelf_item_css(self.shelf.pk))

        def bordered():
            # El color propio del estante es un punto; el del riesgo es un
            # borde izquierdo, para que no se pisen.
            return [
                item for item in self.find_all(".labview-shelf")
                if "border-left" in (item.get_attribute("style") or "")
            ]

        self.assertEqual(bordered(), [])
        self.click("#labview_risk_toggle")
        self.wait_until(bordered, "el overlay no pintó ningún estante")
        self.click("#labview_risk_toggle")
        self.wait_until(
            lambda: not bordered(), "el overlay no se quitó al desactivarlo"
        )

    def test_collapse_all_folds_every_room(self):
        self.open_labview()
        self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
        self.wait_until(
            lambda: self.is_visible(self.room_body_css(self.labroom.pk)),
            "la sala no se desplegó",
        )
        self.click("#labview_collapse_all")
        self.wait_until(
            lambda: not any(
                body.is_displayed() for body in self.find_all(".labview-room-body")
            ),
            "quedó alguna sala desplegada",
        )

    # -- modo edición ------------------------------------------------------

    def test_edit_mode_adds_a_row_and_persists_it(self):
        self.open_labview()
        self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
        before = len(self.find_all(
            "%s .pg-row:not(.pg-head)" % self.furniture_css(self.furniture.pk)))

        self.click('.labview-edit[data-furniture="%d"]' % self.furniture.pk)
        self.click(
            "%s [data-pg-action='add-row']" % self.furniture_css(self.furniture.pk)
        )
        self.wait_until(
            lambda: len(self.find_all(
                "%s .pg-row:not(.pg-head)" % self.furniture_css(self.furniture.pk)
            )) == before + 1,
            "la fila nueva no llegó a la pantalla",
        )

        # Persistencia por operación: no hay un «guardar» que pulsar.
        furniture = Furniture.objects.get(pk=self.furniture.pk)
        self.assertEqual(len(furniture.get_grid()), before + 1)

    def test_removing_an_occupied_row_is_refused_and_repaints_nothing(self):
        """El camino de rechazo: la pantalla se queda con lo que el servidor tiene."""
        self.open_labview()
        self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
        self.click('.labview-edit[data-furniture="%d"]' % self.furniture.pk)

        rows = "%s .pg-row:not(.pg-head)" % self.furniture_css(self.furniture.pk)
        before = len(self.find_all(rows))
        self.click(
            "%s [data-pg-action='remove-row'][data-pg-row='0']"
            % self.furniture_css(self.furniture.pk)
        )
        # El rechazo se ve: `pg:error` abre un Swal con el motivo del servidor.
        popup = self.wait_for(".swal2-popup")
        self.assertIn("refused", popup.text.lower() + popup.text)

        self.assertEqual(len(self.find_all(rows)), before)
        furniture = Furniture.objects.get(pk=self.furniture.pk)
        self.assertEqual(len(furniture.get_grid()), before)

    # -- móvil -------------------------------------------------------------

    def test_a_narrow_viewport_keeps_the_map_and_the_table_usable(self):
        self.selenium.set_window_size(390, 844)
        try:
            self.open_labview()
            self.click("%s .labview-room-toggle" % self.room_css(self.labroom.pk))
            self.click(self.shelf_item_css(self.shelf.pk))
            self.wait_until(
                lambda: "d-none" not in self.find("#labview_table_wrapper")
                .get_attribute("class"),
                "la tabla no se mostró en pantalla angosta",
            )

            # La tabla queda debajo del mapa, no a su lado.
            map_box = self.find("#labview_map").location
            table_box = self.find("#labview_table_wrapper").location
            self.assertGreater(table_box["y"], map_box["y"])

            # Y la página no desborda a lo ancho.
            self.assertLessEqual(
                self.selenium.execute_script(
                    "return document.documentElement.scrollWidth"
                ),
                self.selenium.execute_script(
                    "return document.documentElement.clientWidth"
                ) + 1,
            )
        finally:
            self.selenium.set_window_size(1600, 1200)

    # -- que la vieja siga viva hasta F7 -----------------------------------

    def test_the_old_view_is_still_reachable(self):
        old = reverse(
            "laboratory:rooms_list",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab_pk},
        )
        self.selenium.get(self.live_server_url + old)
        self.assertTrue(
            LaboratoryRoom.objects.filter(laboratory_id=self.lab_pk).exists()
        )
        self.wait_for("#shelfobjecttable, .card")
