"""Cobertura de `laboratory/views/laboratory.py` y `laboratory/views/laboratory_utils.py`.

Recorre las ramas que el resto de la suite no alcanza: el borrado de un
laboratorio desde la organización dueña y desde una organización solo
relacionada, el reporte de códigos H con filtro, y el registro de usuarios por
QR (formulario, alta, reingreso y validaciones de seguridad).
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import (
    Inform,
    Laboratory,
    Object,
    OrganizationStructure,
    OrganizationStructureRelations,
    RegisterUserQR,
    UserOrganization,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.views.laboratory_utils import (
    convert_hcodereport_list,
    convert_hcodereport_table,
    filter_by_user_and_hcode,
    get_function,
)
from sga.models import DangerIndication, SubstanceCharacteristics

XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
PASSWORD = "Clave-Segura-2026"


def add_perms(user, *codenames):
    for codename in codenames:
        app_label, code = codename.split(".")
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=code)
        )


class LaboratoryListAndDeleteTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        add_perms(
            self.user,
            "laboratory.view_laboratory",
            "laboratory.delete_laboratory",
        )
        self.lab_ct = ContentType.objects.get_for_model(Laboratory)
        self.org_related = OrganizationStructure.objects.get(pk=3)

    def test_lista_filtra_por_nombre(self):
        """El parámetro search_fil reduce la lista a los laboratorios que coinciden."""
        url = reverse("laboratory:mylabs", kwargs={"org_pk": self.org.pk})
        response = self.client.get(url, {"search_fil": "Vick"})
        self.assertEqual(response.status_code, 200)
        names = [lab.name for lab in response.context["object_list"]]
        self.assertEqual(names, ["Vick Lab"])

    def test_confirmar_borrado_desde_organizacion_relacionada(self):
        """Desde una organización que solo está relacionada, se avisa que se borra la relación."""
        lab = Laboratory.objects.get(pk=1)
        url = reverse(
            "laboratory:laboratory_delete",
            kwargs={"org_pk": self.org_related.pk, "pk": lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "maintains a relationship with", str(response.context["msg_delete"])
        )

    def test_borrar_desde_organizacion_duena_elimina_relaciones_y_permisos(self):
        """La organización dueña borra el laboratorio, sus relaciones y sus ProfilePermission."""
        lab = Laboratory.objects.get(pk=2)
        # Los Inform del laboratorio se quitan antes: con un objeto relacionado que
        # tiene `name`, get_change_message (laboratory/utils.py) arma tres valores
        # para un mensaje de dos `%s` y el borrado revienta (hallazgo reportado).
        Inform.objects.filter(content_type=self.lab_ct, object_id=lab.pk).delete()
        pp = ProfilePermission.objects.create(
            profile=self.user.profile, content_type=self.lab_ct, object_id=lab.pk
        )
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(
                content_type=self.lab_ct, object_id=lab.pk
            ).exists()
        )
        url = reverse(
            "laboratory:laboratory_delete", kwargs={"org_pk": self.org.pk, "pk": lab.pk}
        )
        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse("laboratory:mylabs", kwargs={"org_pk": self.org.pk}),
            fetch_redirect_response=False,
        )
        self.assertFalse(Laboratory.objects.filter(pk=2).exists())
        self.assertFalse(ProfilePermission.objects.filter(pk=pp.pk).exists())
        self.assertFalse(
            OrganizationStructureRelations.objects.filter(
                content_type=self.lab_ct, object_id=2
            ).exists()
        )

    def test_borrar_desde_organizacion_relacionada_solo_quita_la_relacion(self):
        """Desde una organización relacionada el laboratorio sobrevive; se va la relación y el rol de esa organización."""
        lab = Laboratory.objects.get(pk=1)
        rol_org = self.org_related.rol.first()
        pp = ProfilePermission.objects.create(
            profile=Profile.objects.get(user__username="tuwp"),
            content_type=self.lab_ct,
            object_id=lab.pk,
        )
        pp.rol.add(rol_org)
        url = reverse(
            "laboratory:laboratory_delete",
            kwargs={"org_pk": self.org_related.pk, "pk": lab.pk},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Laboratory.objects.filter(pk=1).exists())
        relations = OrganizationStructureRelations.objects.filter(
            content_type=self.lab_ct, object_id=1
        )
        self.assertFalse(relations.filter(organization=self.org_related).exists())
        self.assertTrue(relations.filter(organization=self.org).exists())
        # Se quita el rol de la organización relacionada (el ProfilePermission vacío
        # queda huérfano: hallazgo reportado en delete_profile_roles_related_to_laboratory).
        self.assertNotIn(rol_org, pp.rol.all())


class HCodeReportTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        add_perms(self.user, "laboratory.do_report")
        self.hcode = DangerIndication.objects.get(code="H314")
        self.reactive = Object.objects.get(pk=2)
        characteristics = SubstanceCharacteristics.objects.create(
            object_related=self.reactive
        )
        characteristics.h_code.add(self.hcode)

    def test_reporte_filtrado_por_codigo_h(self):
        """Con un código H el reporte agrupa por laboratorio los reactivos que lo tienen."""
        url = reverse("laboratory:h_code_reports", kwargs={"org_pk": self.org.pk})
        response = self.client.get(url, {"hcode": [self.hcode.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["params"], "&hcode=H314")
        groups = response.context["object_list"]
        self.assertTrue(groups)
        reactives = [r["reactive"] for g in groups for r in g["reactives"]]
        self.assertIn(self.reactive.name, reactives)
        rooms = {r["room"] for g in groups for r in g["reactives"]}
        self.assertIn(self.lab.laboratoryroom_set.first().name, rooms)

    def test_descarga_en_hoja_de_calculo(self):
        """El formato xlsx usa la conversión en lista con encabezados."""
        url = reverse(
            "laboratory:download_h_code_reports", kwargs={"org_pk": self.org.pk}
        )
        response = self.client.get(url, {"hcode": [self.hcode.pk], "format": "xlsx"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("hcode_report.xlsx", response["Content-Disposition"])

    def test_conversion_en_lista(self):
        """La lista lleva encabezados y una fila por reactivo con sus códigos H."""
        self.assertIs(get_function("convert_hcodereport_list"), convert_hcodereport_list)
        self.assertIs(get_function("otro"), convert_hcodereport_table)
        rows = filter_by_user_and_hcode(
            self.user, [self.hcode], function="convert_hcodereport_list"
        )
        self.assertEqual(len(rows[0]), 7)
        self.assertGreater(len(rows), 1)
        # La columna lleva todos los códigos H del reactivo, separados por coma.
        self.assertTrue(all("H314" in row[6].split(",") for row in rows[1:]))
        # Salen todos los reactivos con ese código H del fixture, entre ellos el creado aquí.
        self.assertIn(self.reactive.name, {row[3] for row in rows[1:]})
        room_names = set(Laboratory.objects.get(pk=1).laboratoryroom_set.values_list("name", flat=True))
        self.assertTrue(all(row[1] in room_names for row in rows[1:]))


class RegisterUserQRBaseTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        add_perms(
            self.user,
            "laboratory.view_registeruserqr",
            "laboratory.add_registeruserqr",
        )
        self.lab_ct = ContentType.objects.get_for_model(Laboratory)
        self.rol = Rol.objects.get(pk=2)
        self.qr = self.make_qr(self.org, self.lab, code="Q001")

    def make_qr(self, org, lab, code, activate_user=True):
        return RegisterUserQR.objects.create(
            created_by=self.user,
            url="http://testserver/qr",
            register_user_qr="qr/test.svg",
            role=self.rol,
            content_type=self.lab_ct,
            object_id=lab.pk,
            organization_creator=self.org,
            organization_register=org,
            code=code,
            activate_user=activate_user,
        )

    def url(self, name, qr=None, org=None, lab=None, **extra):
        qr = qr or self.qr
        kwargs = {
            "org_pk": (org or qr.organization_register).pk,
            "lab_pk": lab.pk if lab else qr.object_id,
            "pk": qr.pk,
        }
        kwargs.update(extra)
        return reverse("laboratory:%s" % name, kwargs=kwargs)

    def register_data(self, email="nuevo@example.com", password=PASSWORD, code=None):
        return {
            "first_name": "Nueva",
            "last_name": "Persona",
            "email": email,
            "phone_number": "8888-0000",
            "id_card": "1-2345-6789",
            "password": password,
            "password_confirm": password,
            "code": code or self.qr.code,
        }


class RegisterUserQRManageTest(RegisterUserQRBaseTest):

    def test_lista_niega_laboratorio_ajeno_a_la_organizacion(self):
        """Un laboratorio que no pertenece a la organización de la URL da 404."""
        url = reverse(
            "laboratory:list_register_user_qr",
            kwargs={"org_pk": 2, "lab_pk": 3},
        )
        response = self.client.get(url, **XHR)
        self.assertEqual(response.status_code, 404)

    def test_crear_con_codigo_repetido_es_invalido(self):
        """Un código ya usado por otro QR no se acepta y no se crea nada."""
        total = RegisterUserQR.objects.count()
        url = reverse(
            "laboratory:manage_register_user_qr",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 0},
        )
        response = self.client.post(
            url,
            {
                "activate_user": True,
                "role": self.rol.pk,
                "organization_register": self.org.pk,
                "organization_creator": self.org.pk,
                "object_id": self.lab.pk,
                "content_type": self.lab_ct.pk,
                "created_by": self.user.pk,
                "code": self.qr.code,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("code", response.context["form"].errors)
        self.assertEqual(RegisterUserQR.objects.count(), total)


class RegisterUserQRFlowTest(RegisterUserQRBaseTest):

    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_pagina_de_ingreso_por_qr(self):
        """La página pública de registro trae los tres formularios y el destino tras el login."""
        response = self.client.get(self.url("login_register_user_qr"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("register_form", response.context)
        self.assertIn("password_form", response.context)
        self.assertEqual(
            response.context["next"], self.url("redirect_user_to_labindex")
        )

    def test_ingreso_con_qr_de_otro_laboratorio_da_404(self):
        """El QR solo sirve para el laboratorio y la organización para los que se emitió."""
        other_lab = Laboratory.objects.get(pk=2)
        response = self.client.get(
            self.url("login_register_user_qr", lab=other_lab), **XHR
        )
        self.assertEqual(response.status_code, 404)

    def test_registro_completo_crea_usuario_y_lo_une_al_laboratorio(self):
        """Datos y código válidos: usuario, perfil, permiso con el rol del QR y membresía."""
        response = self.client.post(self.url("create_user_qr"), self.register_data())
        self.assertRedirects(
            response,
            reverse(
                "laboratory:labindex",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            ),
            fetch_redirect_response=False,
        )
        user = get_user_model().objects.get(username="nuevo@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.profile.id_card, "1-2345-6789")
        self.assertIn(self.lab, user.profile.laboratories.all())
        pp = ProfilePermission.objects.get(
            profile=user.profile, content_type=self.lab_ct, object_id=self.lab.pk
        )
        self.assertIn(self.rol, pp.rol.all())
        self.assertTrue(
            UserOrganization.objects.filter(user=user, organization=self.org).exists()
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registro_con_qr_que_no_activa_usuario(self):
        """Si el QR no activa usuarios, la cuenta queda creada pero inactiva."""
        qr = self.make_qr(self.org, self.lab, code="Q002", activate_user=False)
        data = self.register_data(email="inactivo@example.com", code="Q002")
        self.client.post(self.url("create_user_qr", qr=qr), data)
        user = get_user_model().objects.get(username="inactivo@example.com")
        self.assertFalse(user.is_active)

    def test_registro_en_suborganizacion_suma_la_raiz(self):
        """Registrar en una organización hija también hace miembro de la raíz."""
        child = OrganizationStructure.objects.create(name="Hija", parent=self.org)
        OrganizationStructureRelations.objects.create(
            organization=child, content_type=self.lab_ct, object_id=self.lab.pk
        )
        qr = self.make_qr(child, self.lab, code="Q003")
        data = self.register_data(email="hija@example.com", code="Q003")
        self.client.post(self.url("create_user_qr", qr=qr), data)
        user = get_user_model().objects.get(username="hija@example.com")
        orgs = set(
            UserOrganization.objects.filter(user=user).values_list(
                "organization", flat=True
            )
        )
        self.assertEqual(orgs, {child.pk, self.org.pk})

    def test_correo_existente_no_se_registra(self):
        """Un correo ya usado (como email o como username) se rechaza."""
        for email in ["orgadmin@gmail.com", "admin"]:
            with self.subTest(email=email):
                if email == "admin":
                    get_user_model().objects.filter(username="admin").update(
                        username="ocupado@example.com"
                    )
                    email = "ocupado@example.com"
                response = self.client.post(
                    self.url("create_user_qr"), self.register_data(email=email)
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("email", response.context["register_form"].errors)

    def test_codigo_incorrecto_no_crea_usuario_ni_da_acceso(self):
        """Sin el código del QR no se crea la cuenta ni se otorga el rol en el laboratorio."""
        total = get_user_model().objects.count()
        response = self.client.post(
            self.url("create_user_qr"), self.register_data(code="XXXX")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("code", response.context["password_form"].errors)
        self.assertEqual(get_user_model().objects.count(), total)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registro_con_qr_de_otro_laboratorio_da_404(self):
        """Cambiar el laboratorio de la URL no permite colarse en otro laboratorio."""
        other_lab = Laboratory.objects.get(pk=3)
        total = get_user_model().objects.count()
        response = self.client.post(
            self.url("create_user_qr", lab=other_lab), self.register_data(), **XHR
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(get_user_model().objects.count(), total)

    def test_no_se_puede_tomar_la_cuenta_de_otro_usuario(self):
        """Un anónimo con el código del QR no puede reescribir los datos ni la clave de otro usuario."""
        victim = get_user_model().objects.get(username="admin")
        response = self.client.post(
            self.url("create_user_qr", user=victim.pk),
            self.register_data(email="atacante@example.com"),
            **XHR,
        )
        self.assertEqual(response.status_code, 404)
        victim.refresh_from_db()
        self.assertEqual(victim.username, "admin")
        self.assertFalse(victim.check_password(PASSWORD))

    def test_reintento_del_propio_usuario_con_sesion(self):
        """El usuario autenticado puede completar su propio registro en la ruta con su pk."""
        user = get_user_model().objects.get(username="tuwp")
        self.client.force_login(user)
        response = self.client.post(
            self.url("create_user_qr", user=user.pk),
            self.register_data(email="tuwp@example.com", code="XXXX"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["instance"], user.pk)
        self.assertIn("code", response.context["password_form"].errors)
        user.refresh_from_db()
        self.assertEqual(user.email, "testuserwithoutperms@protonmail.com")

    def test_usuario_completa_sus_datos_con_su_propio_correo(self):
        """Reenviar el propio correo no cuenta como repetido; con el código se fija la clave."""
        user = get_user_model().objects.get(username="tuwp")
        self.client.force_login(user)
        response = self.client.post(
            self.url("create_user_qr", user=user.pk),
            self.register_data(email=user.email),
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.username, "testuserwithoutperms@protonmail.com")
        self.assertTrue(user.check_password(PASSWORD))


class RedirectUserToLabindexTest(RegisterUserQRBaseTest):

    def test_usuario_existente_recibe_el_rol_del_qr(self):
        """Un usuario con perfil que entra por el QR suma el rol al permiso que ya tenía."""
        user = get_user_model().objects.get(username="renatafg")
        pp = ProfilePermission.objects.get(
            profile=user.profile, content_type=self.lab_ct, object_id=self.lab.pk
        )
        self.client.force_login(user)
        response = self.client.get(self.url("redirect_user_to_labindex"))
        self.assertRedirects(
            response,
            reverse(
                "laboratory:labindex",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
            ),
            fetch_redirect_response=False,
        )
        self.assertIn(self.rol, pp.rol.all())
        self.assertTrue(
            UserOrganization.objects.filter(user=user, organization=self.org).exists()
        )

    def test_anonimo_va_al_login(self):
        """Sin sesión no se toca nada: se pide iniciar sesión."""
        self.client.logout()
        response = self.client.get(self.url("redirect_user_to_labindex"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_qr_de_otro_laboratorio_no_da_acceso(self):
        """Un usuario autenticado no puede usar un QR para darse rol en otro laboratorio."""
        user = get_user_model().objects.get(username="tuwp")
        self.client.force_login(user)
        other_lab = Laboratory.objects.get(pk=3)
        response = self.client.get(
            self.url("redirect_user_to_labindex", lab=other_lab), **XHR
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            ProfilePermission.objects.filter(
                profile=user.profile, content_type=self.lab_ct, object_id=3
            ).exists()
        )
