from django.test import tag

from organilab_test.tests.selenium_tests.transversal.base import (
    TransversalSeleniumBase,
)


@tag("selenium")
class PermissionDeniedTest(TransversalSeleniumBase):
    """El desvío que hace `HandleErrorMiddleware` ante un 403.

    Se llega por el camino real: un usuario sin roles visita una página que
    exige permisos. Navegar directo a la ruta comprobaría que la plantilla
    renderiza —eso ya lo hace el smoke—, no que el desvío funcione.

    OJO con el destino, porque no es el que sugiere el nombre de la ruta: el
    middleware NO manda a `authentication:permission_denied`, sino a
    `error_view` con `?status=403` (`authentication/middleware.py:169-185`).
    `permission_denied` sigue existiendo como ruta y con su plantilla, pero
    ningún 403 de navegación acaba ahí.
    """

    def test_permission_denied_flow(self):
        sin_permisos = self.crear_usuario_sin_roles()
        self.force_login(
            user=sin_permisos, driver=self.selenium,
            base_url=self.live_server_url,
        )
        self.navigate("sustance_list", namespace="laboratory",
                      org_pk=self.org_pk, lab_pk=self.lab_pk)
        self.assertIn(
            "status=403", self.selenium.current_url,
            "un usuario sin roles no acabó en la pantalla de error 403, sino "
            "en %s" % self.selenium.current_url,
        )

        # La ruta propia sigue existiendo y renderizando, aunque el middleware
        # no la use: se visita para que no quede sin ninguna prueba.
        self.navigate("permission_denied")

    def crear_usuario_sin_roles(self):
        from django.contrib.auth.models import User

        from auth_and_perms.models import Profile

        usuario, _creado = User.objects.get_or_create(
            username="sin_permisos_selenium",
            defaults={"email": "sin@permisos.test"},
        )
        Profile.objects.get_or_create(user=usuario)
        return usuario
