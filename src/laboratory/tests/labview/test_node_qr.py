# encoding: utf-8
"""QR de salas, muebles y estantes: por URL y creados al pedirlos.

El árbol y la lista de salas ya no generan ni incrustan el SVG; cada nodo trae
la URL de ``laboratory:node_qr_svg``, que crea el QR la primera vez.
"""

from django.contrib.auth.models import Permission
from django.urls import reverse

from laboratory.models import Furniture, LaboratoryRoom, Shelf
from laboratory.qr_nodes import labview_deep_link
from django.contrib.contenttypes.models import ContentType

from auth_and_perms.models import ProfilePermission, Rol
from laboratory.tests.labview.utils import RolPermissionMixin, resolve_permissions
from laboratory.tests.utils import BaseLaboratorySetUpTest
from presentation.models import QRModel

# Sin esta cabecera HandleErrorMiddleware redirige en vez de dejar pasar el 404.
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class NodeQRTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="laboratory",
                codename__in=[
                    "view_laboratoryroom", "view_furniture", "view_shelf",
                    "view_shelfobject",
                ],
            )
        )
        self.user = type(self.user).objects.get(pk=self.user.pk)
        self.client.force_login(self.user)
        self.room = LaboratoryRoom.objects.filter(laboratory=self.lab).first()
        self.furniture = Furniture.objects.filter(labroom=self.room).first()
        self.shelf = Shelf.objects.filter(furniture=self.furniture).first()

    def qr_url(self, kind, pk, lab_pk=None):
        return reverse(
            "laboratory:node_qr_svg",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": lab_pk or self.lab.pk,
                "kind": kind,
                "pk": pk,
            },
        )

    def test_el_qr_se_crea_al_pedirlo_y_una_sola_vez(self):
        QRModel.objects.all().delete()
        response = self.client.get(self.qr_url("shelf", self.shelf.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)
        self.assertEqual(QRModel.objects.count(), 1)

        self.client.get(self.qr_url("shelf", self.shelf.pk))
        self.assertEqual(QRModel.objects.count(), 1)

    def test_el_qr_apunta_al_enlace_profundo_del_labview(self):
        QRModel.objects.all().delete()
        self.client.get(self.qr_url("furniture", self.furniture.pk))
        qr = QRModel.objects.get()
        expected = labview_deep_link(
            self.org.pk, self.lab.pk, labroom=self.room.pk, furniture=self.furniture.pk
        )
        self.assertTrue(qr.qr_url.endswith(expected), qr.qr_url)

    def test_un_qr_viejo_se_rehace_hacia_el_labview(self):
        QRModel.objects.all().delete()
        self.client.get(self.qr_url("labroom", self.room.pk))
        QRModel.objects.update(qr_url="http://testserver/lab/rooms/?labroom=1")
        self.client.get(self.qr_url("labroom", self.room.pk))
        qr = QRModel.objects.get()
        self.assertIn("/labview/", qr.qr_url)

    def test_descarga_como_adjunto(self):
        response = self.client.get(self.qr_url("labroom", self.room.pk) + "?download=1")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_tipo_desconocido_no_existe(self):
        response = self.client.get(self.qr_url("shelfobject", 1), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_un_nodo_de_otro_laboratorio_no_se_sirve(self):
        other = LaboratoryRoom.objects.exclude(laboratory=self.lab).first()
        if other is None:
            self.skipTest("el fixture no trae salas de otro laboratorio")
        response = self.client.get(self.qr_url("labroom", other.pk), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_sin_sesion_no_se_sirve(self):
        self.client.logout()
        response = self.client.get(self.qr_url("labroom", self.room.pk))
        self.assertNotEqual(response.status_code, 200)

    def test_el_arbol_trae_urls_y_no_base64(self):
        url = reverse(
            "laboratory:api-labview-tree-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        QRModel.objects.all().delete()
        tree = self.client.get(url).json()
        room = tree["rooms"][0]
        self.assertEqual(room["qr"], self.qr_url("labroom", room["id"]))
        self.assertFalse(QRModel.objects.exists(), "el árbol no debe generar QR")


class NodeQRPermissionTest(RolPermissionMixin, BaseLaboratorySetUpTest):
    """El QR se autoriza por el Rol del laboratorio, como el resto del labview."""

    def setUp(self):
        super().setUp()
        self.user = self.strip_effective_permissions(self.user)
        self.room = LaboratoryRoom.objects.filter(laboratory=self.lab).first()
        self.url = reverse(
            "laboratory:node_qr_svg",
            kwargs={
                "org_pk": self.org.pk,
                "lab_pk": self.lab.pk,
                "kind": "labroom",
                "pk": self.room.pk,
            },
        )

    def test_sin_ver_salas_no_hay_qr(self):
        self.assertEqual(self.client.get(self.url, **XHR).status_code, 403)

    def test_con_el_rol_de_ver_salas_hay_qr(self):
        # Un Rol canónico (el del catálogo de roles), no uno de prueba: así la
        # sonda de cobertura por rol cuenta este paso como ejercitado.
        rol = Rol.objects.create(name="Administrador de Laboratorio")
        rol.permissions.set(resolve_permissions(["laboratory.view_laboratoryroom"]))
        ProfilePermission.objects.get_or_create(
            profile=self.user.profile,
            content_type=ContentType.objects.get_for_model(self.lab),
            object_id=self.lab.pk,
        )[0].rol.add(rol)
        self.user = self.reload_user(self.user)
        response = self.client.get(self.url, **XHR)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<svg", response.content)
