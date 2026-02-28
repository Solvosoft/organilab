from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap5ReservationsTest(CapacitacionSeleniumBase):
    """Capitulo 5: Sistema de reservaciones de productos de laboratorio."""

    def test_view_reservations(self):
        """Escenario 5.1: Ver listado de reservaciones."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        self.navigate_to_reservations(org_pk=4, status=0)

        path_list = [
            # Esperar a que cargue la tabla de reservaciones
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_reservations_list",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_view_reservations")
