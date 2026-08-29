from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import Rol
from laboratory.models import RegisterUserQR
from laboratory.tests.utils import BaseLaboratorySetUpTest


class RegisterUserQRApiTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        perm = Permission.objects.get(codename="view_registeruserqr")
        self.user.user_permissions.add(perm)
        rol = Rol.objects.first()
        if rol is None:
            rol = Rol.objects.create(name="Rol QR")
        self.qr = RegisterUserQR.objects.create(
            created_by=self.user,
            url="http://example.com/qr",
            register_user_qr="qr/test.png",
            role=rol,
            content_type=ContentType.objects.get(
                app_label="laboratory", model="laboratory"
            ),
            object_id=self.lab.pk,
            organization_creator=self.org,
            organization_register=self.org,
            code="Z999",
        )

    def test_page_renders(self):
        url = reverse(
            "laboratory:list_register_user_qr",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_list(self):
        url = reverse(
            "laboratory:api-registeruserqr-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        rows = {row["id"]: row for row in data["data"]}
        self.assertIn(self.qr.pk, rows)
        self.assertEqual(
            rows[self.qr.pk]["organization_register"], self.org.name
        )

    def test_api_list_excludes_other_lab(self):
        url = reverse(
            "laboratory:api-registeruserqr-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk + 999},
        )
        response = self.client.get(url)
        # El laboratorio no pertenece al usuario: el control multi-tenant
        # responde 404 antes de listar.
        self.assertEqual(response.status_code, 404)

    def test_api_create_not_allowed(self):
        url = reverse(
            "laboratory:api-registeruserqr-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)
