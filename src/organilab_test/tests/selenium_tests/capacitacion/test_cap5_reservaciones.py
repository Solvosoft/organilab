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


@tag("selenium")
class Cap5ManageReservationsTest(CapacitacionSeleniumBase):
    """Capitulo 5: Gestion de reservaciones - aprobacion, rechazo y devolucion."""

    def test_mass_reservation(self):
        """Escenario 5.2: Opcion de reservacion masiva."""
        # Login como docente
        self.login_as(user_pk=4)
        self.navigate_to_reservations(org_pk=4, status=0)

        path_list = [
            # Ver la interfaz de reservaciones con opcion masiva
            {
                "path": "//body",
                "wait_ready": True,
            },
            # Capturar opciones de reservacion masiva
            {
                "path": "//body",
                "screenshot_name": "cap5_mass_reservation",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_mass_reservation")

    def test_approve_reject_reservation(self):
        """Escenario 5.3: Ver detalle de reservacion con opciones aprobar/rechazar."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        self.navigate_to_manage_reservation(org_pk=4, reservation_pk=1)

        path_list = [
            # Capturar detalle de reservacion pendiente con botones aprobar/rechazar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_manage_reservation",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_manage_reservation")

    def test_return_products(self):
        """Escenario 5.4: Formulario de devolucion y cierre de reservacion."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        # Ver reservacion aprobada (pk=2 tiene status=1 Aceptada)
        self.navigate_to_manage_reservation(org_pk=4, reservation_pk=2)

        path_list = [
            # Capturar formulario de devolucion de productos
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_return_products",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_return_products")

        # Capturar vista de reservacion cerrada
        path_list_closed = [
            {
                "path": "//body",
                "screenshot_name": "cap5_reservation_closed",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_closed, "cap5_reservation_closed")
