from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap1RolesAndUsersTest(CapacitacionSeleniumBase):
    """Capitulo 1: Verificacion de permisos de usuarios."""

    def test_verify_user_permissions(self):
        """Escenario 1.7: Verificar permisos con diferentes usuarios."""
        # Login como estudiante
        self.login_as(user_pk=5)
        self.navigate_to_my_labs(org_pk=4)

        path_list_student = [
            # Ver la interfaz del estudiante - acceso limitado
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap1_student_view",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_student, "cap1_verify_permissions_student")

        # Login como gestor de laboratorio
        self.login_as(user_pk=2)
        self.navigate_to_my_labs(org_pk=4)

        path_list_manager = [
            # Ver la interfaz del gestor - acceso ampliado
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap1_manager_view",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_manager, "cap1_verify_permissions")
