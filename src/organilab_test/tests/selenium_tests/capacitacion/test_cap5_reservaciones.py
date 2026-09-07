from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)
from organilab_test.tests.selenium_xpaths import (
    PAGE_MANAGE_RESERVATION,
    PAGE_RESERVATIONS_LIST,
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
                "path": PAGE_RESERVATIONS_LIST,
                "wait_ready": True,
                "screenshot_name": "cap5_reservations_list",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_view_reservations")


@tag("selenium")
class Cap5MyReservationsTest(CapacitacionSeleniumBase):
    """Capitulo 5: Vista de mis reservaciones pendientes y accion de reservar."""

    def test_my_reservations_and_reserve(self):
        """Escenario 5.5: Ver productos pendientes y presionar el boton Reservar."""
        # Login como docente (tiene productos en estado SELECTED)
        self.login_as(user_pk=4)
        self.navigate_to_my_reservations(org_pk=4, lab_pk=1)

        path_list = [
            # Capturar la tabla con productos pendientes y boton Reservar habilitado
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_my_reservations_pending",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Reservar
            {
                "path": "//input[@id='reserve_btn']",
                "wait_ready": True,
            },
            # Capturar el resultado despues de enviar la reserva
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_my_reservations_after_reserve",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_my_reservations_reserve")


@tag("selenium")
class Cap5ManageReservationsTest(CapacitacionSeleniumBase):
    """Capitulo 5: Gestion de reservaciones - aprobacion, rechazo y devolucion."""

    def test_mass_reservation(self):
        """Escenario 5.2: Opcion de reservacion masiva."""
        # Login como docente
        self.login_as(user_pk=2)
        self.navigate_to_reservations(org_pk=4, status=0)

        path_list = [
            # Ver la interfaz de reservaciones con opcion masiva
            {
                "path": PAGE_RESERVATIONS_LIST,
                "wait_ready": True,
            },
            # Capturar opciones de reservacion masiva
            {
                "path": PAGE_RESERVATIONS_LIST,
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
                "path": PAGE_MANAGE_RESERVATION,
                "wait_ready": True,
                "screenshot_name": "cap5_manage_reservation",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_manage_reservation")

    def test_approve_reservation_flow(self):
        """Escenario 5.6: Flujo completo - ir al listado, abrir gestion y aprobar reservacion."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        self.navigate_to_reservations(org_pk=4, status=0)

        path_list = [
            # Capturar listado de reservaciones solicitadas
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_approve_flow_list",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Administrar de la primera reservacion
            {
                "path": "//a[@title='Administrar']",
            },
            # Capturar detalle de la reservacion con botones Aceptar/Rechazar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_approve_flow_manage",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Aceptar general de la reservacion
            {
                "path": "//button[@name='action' and @value='accept']",
            },
            # Capturar resultado tras aceptar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_approve_flow_result",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_approve_reservation_flow")

    def test_return_product_flow(self):
        """Escenario 5.4: Flujo completo - ir al listado aceptadas, abrir gestion y devolver producto."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        self.navigate_to_reservations(org_pk=4, status=1)

        path_list = [
            # Capturar listado de reservaciones aceptadas
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_return_flow_list",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Administrar
            {
                "path": "//a[@title='Administrar']",
            },
            # Capturar la vista de gestion con el boton Devolver
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_return_flow_manage",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Devolver (abre modal con formulario via AJAX)
            {
                "path": "//button[contains(@onclick, 'openReturnModal')]",
            },
            # Esperar a que cargue el formulario en el modal
            {
                "path": "//input[@id='returnAmountInput']",
                "wait_ready": True,
                "screenshot_name": "cap5_return_flow_modal",
                "extra_action": "script",
                "value": "",
            },
            # Ingresar la cantidad a devolver
            {
                "path": "//input[@id='returnAmountInput']",
                "extra_action": "setvalue",
                "value": "1",
            },
            # Confirmar la devolucion
            {
                "path": "//button[@id='confirmReturnBtn']",
            },
            # Capturar resultado tras la devolucion
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_return_flow_result",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_return_product_flow")

    def test_close_reservation_flow(self):
        """Escenario 5.7: Cerrar una reservacion aceptada desde el listado."""
        self.login_as(user_pk=2)
        self.navigate_to_reservations(org_pk=4, status=1)

        path_list = [
            # Capturar listado de reservaciones aceptadas
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_close_flow_list",
                "extra_action": "script",
                "value": "",
            },
            # Presionar el boton Cerrar y confirmar la alerta
            {
                "path": "//button[contains(@class, 'btn-close-reservation')]",
                "extra_action": "sweetalert_comfirm",
                "comfirm": "var btn = document.querySelector('.swal2-confirm'); if(btn) btn.click();",
            },
            # Capturar resultado tras cerrar la reservacion
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap5_close_flow_result",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap5_close_reservation_flow")

    def test_return_products(self):
        """Escenario 5.4: Formulario de devolucion y cierre de reservacion."""
        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        # Ver reservacion aprobada (pk=2 tiene status=1 Aceptada)
        self.navigate_to_manage_reservation(org_pk=4, reservation_pk=2)

        path_list = [
            # Capturar formulario de devolucion de productos
            {
                "path": PAGE_MANAGE_RESERVATION,
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
                "path": PAGE_MANAGE_RESERVATION,
                "screenshot_name": "cap5_reservation_closed",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_closed, "cap5_reservation_closed")
