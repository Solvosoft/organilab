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
                "path": "//span[contains(text(),'Departamento de Quimica')]",
                "sleep": 1,
            },
            # Capturar el popup de opciones de gestion
            {
                "path": "//body",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "cap1_org_popup")

    def test_delete_user_relations(self):
        """Escenario 1.4: Eliminar relaciones usuario-laboratorio y usuario-organizacion."""
        self.navigate_to_org_manage()

        # Navegar al tab de laboratorio del usuario
        path_list_lab = [
            # Hacer clic en organizacion
            {
                "path": "//span[contains(text(),'Departamento de Quimica')]",
                "sleep": 1,
            },
            # Abrir gestion de usuarios (boton de usuarios en popup)
            {
                "path": "//a[contains(@href,'profilepermission') or contains(text(),'Usuarios')]",
                "wait_ready": True,
                "sleep": 1,
            },
            # Capturar vista de relaciones usuario-laboratorio
            {
                "path": "//body",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list_lab, "cap1_delete_user_lab_relation")

        # Vista de relaciones usuario-organizacion
        path_list_org = [
            # Cambiar a tab de organizacion
            {
                "path": "//a[@href='#tab_org' or contains(text(),'Organizaci')]",
                "sleep": 1,
            },
            # Capturar vista
            {
                "path": "//body",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list_org, "cap1_delete_user_org_relation")

    def test_manage_permission_groups(self):
        """Escenario 1.4: Administrar grupos de permisos por perfil."""
        self.navigate_to_org_manage()

        path_list = [
            # Navegar a gestion de organizacion
            {
                "path": "//span[contains(text(),'Departamento de Quimica')]",
                "sleep": 1,
            },
            # Abrir vista de perfiles/permisos
            {
                "path": "//a[contains(@href,'profilepermission') or contains(text(),'Usuarios')]",
                "wait_ready": True,
                "sleep": 1,
            },
            # Capturar la vista de grupos de permisos
            {
                "path": "//body",
                "sleep": 1,
                "screenshot_name": "cap1_manage_permission_groups",
            },
        ]
        self.create_gif_process(path_list, "cap1_manage_permission_groups")


@tag("selenium")
class Cap1RiskZonesTest(CapacitacionSeleniumBase):
    """Capitulo 1: Zonas de riesgo con laboratorios asociados."""

    def test_view_risk_zones(self):
        """Escenario 1.6: Ver zonas de riesgo con laboratorios asociados."""
        self.navigate_to_risk_zone_list(org_pk=4)

        path_list = [
            # Capturar vista de zonas de riesgo
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap1_risk_zones_labs",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap1_risk_zones_labs")
