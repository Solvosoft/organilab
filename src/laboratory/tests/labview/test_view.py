"""La pantalla del labview: que renderiza y que respeta el contrato del deep-link."""

from django.contrib.auth.models import Permission
from django.urls import reverse

from auth_and_perms.models import Rol
from laboratory.models import Shelf
from laboratory.tests.utils import BaseLaboratorySetUpTest


class LabviewViewTest(BaseLaboratorySetUpTest):
    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="laboratory",
                codename__in=["view_laboratoryroom", "view_shelfobject"],
            )
        )
        self.client.force_login(self.user)
        self.url = reverse(
            "laboratory:labview",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )

    def test_the_page_renders_with_its_scripts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for asset in [
            "labview/labview_state.js",
            "labview/labview_render.js",
            "labview/labview_search.js",
            "labview/labview_actions.js",
            "labview/labview_editor.js",
            "labview/labview.js",
            # Los modales de accion se reutilizan tal cual, no se reescriben.
            "shelfobject_action_helpers.js",
            "base_modal_management.js",
        ]:
            self.assertIn(asset, content, asset)
        self.assertIn('id="labview_map"', content)
        # Los botones de cabecera de la tabla (crear objeto, contenedores,
        # transferencias entrantes) y la tabla de transferencias viven en el
        # codigo compartido y necesitan estas dos piezas del contexto.
        self.assertIn("can_add_shelfobject", content)
        self.assertIn('id="transfer-list-datatable"', content)
        self.assertIn("transfer_list", content)
        self.assertIn('id="labview_shelfobjecttable"', content)
        # Un solo contenedor de detalle en toda la pagina, no uno por fila.
        self.assertEqual(content.count('id="detail_modal_container"'), 1)

    def test_deep_link_is_resolved_upwards_on_the_server(self):
        shelf = Shelf.objects.get(pk=1)
        response = self.client.get(self.url + "?shelf=%d" % shelf.pk)
        self.assertEqual(response.status_code, 200)
        state = response.context["search_by_url"]
        self.assertEqual(state["shelf"]["shelf"], [shelf.pk])
        self.assertEqual(state["furniture"]["furniture"], [shelf.furniture_id])
        self.assertEqual(state["labroom"], [shelf.furniture.labroom_id])

    def test_an_invalid_deep_link_is_refused(self):
        # HandleErrorMiddleware convierte el 404 de una peticion HTML en una
        # redireccion a la pagina de error; con la cabecera de XHR se ve el
        # codigo real.
        response = self.client.get(
            self.url + "?shelf=999999", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 404)

    def test_the_old_view_still_works(self):
        """rooms_list queda intacta hasta que Luis valide la nueva."""
        old = reverse(
            "laboratory:rooms_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertEqual(self.client.get(old).status_code, 200)

    def test_without_permission_the_page_is_refused(self):
        for rol in Rol.objects.all():
            rol.permissions.clear()
        self.user.user_permissions.clear()
        self.user.groups.clear()
        self.client.force_login(type(self.user).objects.get(pk=self.user.pk))
        response = self.client.get(
            self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 403)
