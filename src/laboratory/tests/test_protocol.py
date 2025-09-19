from django.contrib.auth.models import Permission
from django.urls import reverse

from auth_and_perms.models import ProfilePermission, Rol
from laboratory.models import Protocol
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json


class ProtocolViewTest(BaseLaboratorySetUpTest):
    def get_permissions_by_contenttype(self, permname):
        appname, codename = permname.split(".")
        return Permission.objects.get(
            content_type__app_label=appname, codename=codename
        )

    def setUp(self):
        super().setUp()

        self.permissions = ProfilePermission.objects.filter(
            content_type__app_label="laboratory",
            object_id=self.lab.pk,
            profile=self.user.profile,
        ).first()
        self.permissions.rol.clear()
        self.rol = Rol.objects.create(name="Protocol user")
        self.permissions.rol.add(self.rol)
        self.add_permission = self.get_permissions_by_contenttype(
            "laboratory.add_protocol"
        )
        self.update_permission = self.get_permissions_by_contenttype(
            "laboratory.change_protocol"
        )
        self.delete_permission = self.get_permissions_by_contenttype(
            "laboratory.delete_protocol"
        )
        self.view_permission = self.get_permissions_by_contenttype(
            "laboratory.view_protocol"
        )

    def test_protocol_list(self):
        self.rol.permissions.add(self.view_permission)
        # This view is just a container(table), protocol table loads by "laboratory:api-protocol-list"
        url = reverse(
            "laboratory:protocol_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, template_name="laboratory/protocol/protocol_list.html"
        )
        self.rol.permissions.remove(self.view_permission)

    def test_update_protocol(self):
        self.rol.permissions.add(self.update_permission)

        protocol = Protocol.objects.get(name="Lavado de manos")
        url = reverse(
            "laboratory:protocol_update",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": protocol.pk},
        )

        # Checking by method get if initial data protocol exists
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Lavado de manos")

        # Updating protocol
        data = {
            "name": "Lavado de manos",
            "short_description": "Higienización de las manos previa al ingreso del laboratorio y manipulación de los instrumentos del mismo.",
            "file": self.chfile.upload_id,
            "laboratory": self.lab,
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse(
            "laboratory:protocol_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertRedirects(response_post, success_url)
        self.rol.permissions.remove(self.update_permission)

    def test_create_protocol(self):
        self.rol.permissions.add(self.add_permission)
        data = {
            "name": "Manejo de desechos",
            "short_description": "Manipulación de desechos ordinarios y reciclables y su destino.",
            "file": json.dumps(
                {
                    "token": self.chfile.upload_id,
                    "name": "protocol.pdf",
                    "display_text": "protocol_test.pdf",
                }
            ),
        }
        url = reverse(
            "laboratory:protocol_create",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.post(url, data=data)
        success_url = reverse(
            "laboratory:protocol_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertRedirects(response, success_url)
        self.assertIn(
            "Manejo de desechos", list(Protocol.objects.values_list("name", flat=True))
        )
        self.rol.permissions.remove(self.add_permission)

    def test_delete_protocol(self):
        self.rol.permissions.add(self.delete_permission)
        protocol = Protocol.objects.get(
            name="Manipulación de instrumentos de laboratorio"
        )
        url = reverse(
            "laboratory:protocol_delete",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": protocol.pk},
        )
        response = self.client.post(url)
        success_url = reverse(
            "laboratory:protocol_list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
        self.assertNotIn(
            "Manipulación de instrumentos de laboratorio",
            list(Protocol.objects.values_list("name", flat=True)),
        )
        self.rol.permissions.remove(self.delete_permission)

    def test_api_protocol_list_set_limit(self):
        url = reverse("laboratory:api-protocol-list")
        response = self.client.get(
            url,
            data={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "offset": 0,
                "limit": 10,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Control de plagas")

    def test_api_protocol_list_default_limit(self):
        url = reverse("laboratory:api-protocol-list")
        response = self.client.get(
            url, data={"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Control de plagas", response.content.decode())
