from django.test import tag

from organilab_test.tests.selenium_tests.transversal.base import (
    TransversalSeleniumBase,
)
from organilab_test.tests.selenium_xpaths import datatable_search_input


@tag("selenium")
class UsersAndLabOrgListsTest(TransversalSeleniumBase):
    """Las tres pantallas de `auth_and_perms` que no tenían prueba.

    `get_users` (filtros y modales de detalle por organización y por
    laboratorio), `lab_org_list` (dos pestañas con su tabla cada una) y
    `map_of_laboratories`. Son de solo consulta, así que van juntas en un
    recorrido y ninguna necesita `@modifies_db`.
    """

    def test_users_and_lab_org_lists_flow(self):
        # 1. Listado de usuarios: tabla, filtro y limpieza del filtro.
        self.navigate("get_users", namespace="auth_and_perms")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='user_table']", "presence_only": True,
                 "wait_dt": True},
                {"path": datatable_search_input("user_table"),
                 "extra_action": "setvalue", "value": "a"},
                {"path": "//*[@id='user_table']", "presence_only": True,
                 "wait_dt": True},
                {"path": "//*[@id='btn-clear-filters']"},
                {"path": "//*[@id='user_table']", "presence_only": True,
                 "wait_dt": True},
            ],
            "auth_user_list",
        )

        # 2. Laboratorios y organizaciones: las dos pestañas y sus tablas.
        self.navigate("lab_org_list", namespace="auth_and_perms")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='navbylabs']"},
                {"path": "//*[@id='labtable']", "presence_only": True,
                 "wait_dt": True},
                {"path": "//*[@id='navbyorgs']"},
                {"path": "//*[@id='orgtable']", "presence_only": True,
                 "wait_dt": True},
            ],
            "auth_lab_org_list",
        )

        # 3. Mapa de laboratorios.
        self.navigate("map_of_laboratories", namespace="auth_and_perms",
                      org_pk=self.org_pk)
