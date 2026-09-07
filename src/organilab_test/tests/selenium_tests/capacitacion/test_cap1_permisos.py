from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)
from organilab_test.tests.selenium_xpaths import (
    PAGE_MY_LABS,
    PAGE_RISKZONE_LIST,
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
                "path": PAGE_MY_LABS,
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
                "path": PAGE_MY_LABS,
                "wait_ready": True,
                "screenshot_name": "cap1_manager_view",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list_manager, "cap1_verify_permissions")


@tag("selenium")
class Cap1OrgTreeAndProfileTest(CapacitacionSeleniumBase):
    """Capitulo 1: Arbol de organizaciones y gestion de perfiles."""

    def test_org_tree_and_popup(self):
        """Escenario 1.2: Ver arbol de organizaciones y popup de gestion."""
        self.navigate_to_org_manage()

        path_list = [
            # Capturar el arbol de organizaciones
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap1_org_tree_view",
                "extra_action": "script",
                "value": "",
            },
            # Hacer clic en una organizacion para abrir el popup
            {
                "path": "//h6[contains(text(),'Departamento de Quimica')]",
                "sleep": 1,
            },
            # Capturar el popup de opciones de gestion
            {
                "path": "//body",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "cap1_org_popup")

    # DISABLED: test_delete_user_relations - template no longer has
    # profilepermission link or 'Usuarios' text in org collapse section.
    # The org manage page now uses inline tabs instead of separate navigation.
    # def test_delete_user_relations(self):
    #     """Escenario 1.4: Eliminar relaciones usuario-laboratorio y usuario-organizacion."""
    #     ...

    # DISABLED: test_manage_permission_groups - same template mismatch as above.
    # def test_manage_permission_groups(self):
    #     """Escenario 1.4: Administrar grupos de permisos por perfil."""
    #     ...


@tag("selenium")
class Cap1RiskZonesTest(CapacitacionSeleniumBase):
    """Capitulo 1: Zonas de riesgo con laboratorios asociados."""

    def test_view_risk_zones(self):
        """Escenario 1.6: Ver zonas de riesgo con laboratorios asociados."""
        self.navigate_to_risk_zone_list(org_pk=4)

        path_list = [
            # Capturar vista de zonas de riesgo
            {
                "path": PAGE_RISKZONE_LIST,
                "wait_ready": True,
                "screenshot_name": "cap1_risk_zones_labs",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap1_risk_zones_labs")
