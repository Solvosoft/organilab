from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)
from organilab_test.tests.selenium_xpaths import (
    FLASH_SUCCESS,
    PAGE_ADMIN_CHANGELIST,
    PAGE_REPORT_INDEX,
)


@tag("selenium")
class Cap6TasksTest(CapacitacionSeleniumBase):
    """Capitulo 6: Tareas programadas y mantenimiento del sistema."""

    def test_block_expiration_notifications(self):
        """Escenario 6.1: Bloquear notificaciones de expiracion de un producto."""
        self.navigate_to_block_notification(lab_pk=1, obj_pk=1)

        path_list = [
            # Capturar vista de bloqueo de notificaciones
            {
                "path": FLASH_SUCCESS,
                "wait_ready": True,
                "screenshot_name": "cap6_block_notifications",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap6_block_notifications")

    def test_establishment_reports_list(self):
        """Escenario 6.2: Ver listado de reportes de establecimientos."""
        self.navigate_to_reports(org_pk=4)

        path_list = [
            # Capturar vista de reportes (incluye establecimientos)
            {
                "path": PAGE_REPORT_INDEX,
                "wait_ready": True,
                "screenshot_name": "cap6_establishment_reports",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap6_establishment_reports")

    def test_admin_celery_tasks(self):
        """Escenario 6.3: Panel de administracion con tareas de mantenimiento."""
        # Login como superusuario (pk=1 es admin_university, is_superuser=True)
        self.navigate_to_admin("django_celery_beat/periodictask/")

        path_list = [
            # Capturar panel de admin con tareas periodicas
            {
                "path": PAGE_ADMIN_CHANGELIST,
                "sleep": 2,
                "screenshot_name": "cap6_admin_maintenance",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap6_admin_maintenance")
