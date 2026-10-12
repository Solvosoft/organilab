"""API de `auth_and_perms` (`api/viewsets.py` y los validadores de `api/serializers.py`):
resultados, errores de validación y aislamiento entre organizaciones."""

import json

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group
from django.urls import reverse

from auth_and_perms.models import ProfilePermission, Rol
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from laboratory.models import Laboratory, OrganizationStructureRelations, UserOrganization


class APIBase(EscenarioOrganizaciones):
    def setUp(self):
        self.admin_a = self.crear_usuario(
            "admin-a",
            self.org_a,
            perms=[
                "laboratory.view_laboratory",
                "laboratory.view_organizationstructure",
                "auth_and_perms.view_profile",
                "auth_and_perms.can_add_external_user_in_org",
                "laboratory.view_organizationstructurerelations",
                "laboratory.delete_organizationstructurerelations",
            ],
            ambito="perfil",
        )
        self.miembro_a = self.crear_usuario("miembro-a", self.org_a)
        self.miembro_b = self.crear_usuario("miembro-b", self.org_b)
        self.client.force_login(self.admin_a)

    def put_json(self, url, data):
        return self.client.put(url, data=json.dumps(data), content_type="application/json")


class RelacionDeUsuarioConObjetoTest(APIBase):
    url = "/perms/api/relusertocontenttype/"

    def test_laboratorio_de_otra_organizacion_se_niega(self):
        response = self.client.post(
            reverse("auth_and_perms:api-relusertocontenttype-list"),
            data={
                "typeofcontenttype": "laboratory",
                "user": self.miembro_a.pk,
                "organization": self.org_a.pk,
                "laboratory": self.lab_b.pk,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            ProfilePermission.objects.filter(profile=self.miembro_a.profile, object_id=self.lab_b.pk).exists()
        )


class RolesPorPerfilTest(APIBase):
    def setUp(self):
        super().setUp()
        self.rol = Rol.objects.create(name="Rol de la raíz A")
        self.org_a.rol.add(self.rol)
        self.url = reverse("auth_and_perms:api-rolbyorg-detail", args=[self.org_a.pk])

    def datos(self, contenttypeobj, accion="append"):
        return {
            "rols": [self.rol.pk],
            "as_conttentype": False,
            "as_user": False,
            "as_role": True,
            "profile": self.miembro_a.profile.pk,
            "contenttypeobj": contenttypeobj,
            "mergeaction": accion,
        }

    def test_laboratorio_que_la_organizacion_no_puede_cambiar_da_403(self):
        response = self.put_json(
            self.url,
            self.datos({"org": self.org_a.pk, "appname": "laboratory", "model": "laboratory", "objectid": self.lab_b.pk}),
        )
        self.assertNegado(response, 403)
        self.assertFalse(ProfilePermission.objects.filter(object_id=self.lab_b.pk).exists())

    def test_sin_objeto_el_rol_se_asigna_sobre_el_perfil(self):
        response = self.put_json(
            self.url, self.datos({"org": self.org_a.pk, "appname": "laboratory", "model": "organizationstructure"})
        )
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.get(
            profile=self.miembro_a.profile, content_type=self.ct_profile, object_id=self.miembro_a.profile.pk
        )
        self.assertEqual(list(pp.rol.all()), [self.rol])

    def test_datos_invalidos_devuelven_los_errores(self):
        response = self.put_json(self.url, {"mergeaction": "otra"})
        self.assertIn("mergeaction", response.json())
        self.assertIn("rols", response.json())


class UsuariosDeLaboratorioTest(APIBase):
    def test_laboratorio_ajeno_a_la_organizacion_da_403(self):
        response = self.client.get(
            reverse("auth_and_perms:api-prolaborg-list"),
            {"organization": self.org_a.pk, "laboratory": self.lab_b.pk},
        )
        self.assertNegado(response, 403)


class HeredarPerfilTest(APIBase):
    url = "/perms/api/profileinorgrol/inerit_profile/"

    def test_hereda_los_roles_de_la_organizacion_a_sus_hijas(self):
        rol = Rol.objects.create(name="Heredable")
        self.org_a.rol.add(rol)
        pp = ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_org, object_id=self.org_a.pk
        )
        pp.rol.add(rol)
        response = self.client.post(
            reverse("auth_and_perms:api-userinorg-inerit-profile"),
            data={
                "profile": self.miembro_a.profile.pk,
                "organization": self.org_a.pk,
                "app_label": "laboratory",
                "model": "organizationstructure",
                "object_id": self.org_a.pk,
            },
        )
        self.assertEqual(response.json(), {"result": "ok"})
        hija = ProfilePermission.objects.get(profile=self.miembro_a.profile, object_id=self.org_a_hija.pk)
        self.assertEqual(list(hija.rol.all()), [rol])
        self.assertIn(rol, self.org_a_hija.rol.all())
        self.assertTrue(self.org_a_hija.users.filter(pk=self.miembro_a.pk).exists())

    def test_datos_invalidos_dan_400(self):
        response = self.client.post(reverse("auth_and_perms:api-userinorg-inerit-profile"), data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("profile", response.json())


class UsuarioExternoTest(APIBase):
    def test_buscar_correo_inexistente_da_400(self):
        response = self.put_json(
            reverse("auth_and_perms:api-extuserinorg-detail", args=[self.org_a.pk]),
            {"email": "nadie@ejemplo.cr", "organization": self.org_a.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])

    def test_buscar_un_usuario_que_ya_es_miembro_da_400(self):
        response = self.put_json(
            reverse("auth_and_perms:api-extuserinorg-detail", args=[self.org_a.pk]),
            {"email": self.miembro_a.email, "organization": self.org_a.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])

    def agregar(self, email, pk):
        return self.client.post(
            reverse("auth_and_perms:api-extuserinorg-list"),
            data={"email": email, "pk": pk, "organization": self.org_a.pk},
        )

    def test_agregar_valida_correo_membresia_y_coincidencia(self):
        casos = [
            ("nadie@ejemplo.cr", self.miembro_b.pk),
            (self.miembro_a.email, self.miembro_a.pk),
            (self.miembro_b.email, self.miembro_a.pk),
        ]
        for email, pk in casos:
            with self.subTest(email=email):
                response = self.agregar(email, pk)
                self.assertEqual(response.json(), {"success": False})
        self.assertFalse(self.org_a.users.filter(pk=self.miembro_b.pk).exists())


class QuitarUsuarioDeOrganizacionTest(APIBase):
    def test_quitar_de_una_organizacion_hija_solo_afecta_a_esa(self):
        UserOrganization.objects.create(user=self.miembro_a, organization=self.org_a_hija)
        ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_org, object_id=self.org_a_hija.pk
        )
        response = self.client.delete(
            reverse("auth_and_perms:api-deluserorgcontt-list"),
            data=json.dumps(
                {
                    "profile": self.miembro_a.profile.pk,
                    "app_label": "laboratory",
                    "model": "organizationstructure",
                    "object_id": self.org_a_hija.pk,
                    "organization": self.org_a_hija.pk,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.json(), {"result": "ok"})
        self.assertFalse(self.org_a_hija.users.filter(pk=self.miembro_a.pk).exists())
        self.assertTrue(self.org_a.users.filter(pk=self.miembro_a.pk).exists())


class GruposPorPerfilTest(APIBase):
    def test_quitar_un_grupo_queda_en_la_bitacora(self):
        viejo = Group.objects.create(name="Grupo viejo")
        nuevo = Group.objects.create(name="Grupo nuevo")
        self.miembro_a.groups.add(viejo)
        response = self.client.post(
            reverse("auth_and_perms:api_update_groups_by_profile"),
            data={"organization": self.org_a.pk, "profile": self.miembro_a.pk, "groups": [nuevo.pk]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.miembro_a.groups.all()), [nuevo])
        self.assertTrue(LogEntry.objects.filter(change_message__contains="Grupo viejo").exists())


class GeolocalizacionTest(APIBase):
    def test_coordenadas_invalidas_se_omiten(self):
        Laboratory.objects.filter(pk=self.lab_a.pk).update(geolocation="no-es-coordenada")
        Laboratory.objects.filter(pk=self.lab_a_hija.pk).update(geolocation="9.93,-84.08")
        response = self.client.get(reverse("auth_and_perms:api_laboratory_geolocations"))
        nombres = [lab["lab"] for lab in response.json()["laboratories"]]
        self.assertIn("Laboratorio A hija", nombres)
        self.assertNotIn("Laboratorio A", nombres)


class LaboratoriosDeOrganizacionTest(APIBase):
    def setUp(self):
        super().setUp()
        self.otro_lab = Laboratory.objects.create(name="Otro de A", organization=self.org_a)
        self.url = reverse("auth_and_perms:manage_org_labs", args=[self.org_a_hija.pk])
        OrganizationStructureRelations.objects.create(
            organization=self.org_a_hija, content_type=self.ct_lab, object_id=self.lab_a.pk
        )

    def vinculados(self):
        return set(
            OrganizationStructureRelations.objects.filter(
                organization=self.org_a_hija, content_type=self.ct_lab
            ).values_list("object_id", flat=True)
        )

    def test_reemplazar_los_laboratorios(self):
        self.put_json(self.url, {"labs": [self.otro_lab.pk], "mergeaction": "full"})
        self.assertEqual(self.vinculados(), {self.otro_lab.pk})

    def test_desvincular_laboratorios(self):
        self.put_json(self.url, {"labs": [self.lab_a.pk], "mergeaction": "sustract"})
        self.assertEqual(self.vinculados(), set())

    def test_accion_desconocida_no_cambia_nada(self):
        response = self.put_json(self.url, {"labs": [self.otro_lab.pk], "mergeaction": "otra"})
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(self.vinculados(), {self.lab_a.pk})


class ListadosDePlataformaTest(APIBase):
    def test_usuarios_filtrados_por_organizacion_y_rol(self):
        rol = ProfilePermission.objects.get(profile=self.admin_a.profile).rol.get()
        response = self.client.get(
            reverse("auth_and_perms:api-userlist-list"), {"organization": self.org_a.pk, "roles[]": [rol.pk]}
        )
        self.assertEqual([fila["username"] for fila in response.json()["data"]], ["admin-a"])

    def test_sin_permiso_los_listados_de_plataforma_se_niegan(self):
        self.client.force_login(self.miembro_a)
        for nombre in ("auth_and_perms:api-orglablist-list", "auth_and_perms:api-laborglist-list"):
            with self.subTest(nombre=nombre):
                response = self.client.get(reverse(nombre))
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json())

    def test_roles_por_laboratorio_y_organizacion(self):
        rol = Rol.objects.create(name="Laboratorista")
        pp = ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_lab, object_id=self.lab_a.pk, organization=self.org_a
        )
        pp.rol.add(rol)
        response = self.client.get(
            reverse("auth_and_perms:api-laborgroles-list"),
            {"organization": self.org_a.pk, "laboratory": self.lab_a.pk},
        )
        self.assertEqual(response.json(), [{"user": "miembro-a", "roles": "Laboratorista"}])
        response = self.client.get(reverse("auth_and_perms:api-laborgroles-list"))
        self.assertEqual(response.json(), [])

    def test_roles_de_un_usuario_en_organizacion(self):
        rol = Rol.objects.create(name="Gestor")
        pp = ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_org, object_id=self.org_a.pk
        )
        pp.rol.add(rol)
        url = reverse("auth_and_perms:api-userroles-roles-in-organization", kwargs={"user_pk": self.miembro_a.pk})
        self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(self.client.get(url, {"organization": self.org_a.pk}).json(), {"roles": ["Gestor"]})
        self.assertEqual(self.client.get(url, {"organization": self.org_a_hija.pk}).json(), {"roles": []})

    def test_roles_de_un_usuario_en_laboratorio(self):
        rol = Rol.objects.create(name="Encargado")
        pp = ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_lab, object_id=self.lab_a.pk, organization=self.org_a
        )
        pp.rol.add(rol)
        url = reverse("auth_and_perms:api-userroles-roles-in-laboratory", kwargs={"user_pk": self.miembro_a.pk})
        response = self.client.get(url, {"laboratory": self.lab_a.pk})
        self.assertEqual(response.json(), {"data": [{"org_name": "Organización A", "roles": ["Encargado"]}]})


class RelacionesOrganizacionLaboratorioTest(APIBase):
    def test_listar_relaciones_de_una_organizacion_ajena_se_niega(self):
        OrganizationStructureRelations.objects.create(
            organization=self.org_b, content_type=self.ct_lab, object_id=self.lab_b.pk
        )
        response = self.client.get(
            reverse("auth_and_perms:api-org-lab-relation-list", kwargs={"org_pk": self.org_b.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_borrar_relacion_con_laboratorio_inexistente(self):
        relacion = OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_lab, object_id=999999
        )
        response = self.client.delete(
            reverse(
                "auth_and_perms:api-org-lab-relation-detail",
                kwargs={"org_pk": self.org_a.pk, "pk": relacion.pk},
            )
        )
        self.assertIn(response.status_code, (200, 204))
        self.assertFalse(OrganizationStructureRelations.objects.filter(pk=relacion.pk).exists())
        self.assertTrue(LogEntry.objects.filter(change_message__contains="999999").exists())


class BusquedaDePerfilesTest(APIBase):
    def test_busqueda_global_en_el_listado_de_miembros(self):
        # La búsqueda global mira nombre y apellidos, no el username.
        self.miembro_a.first_name = "Miembro"
        self.miembro_a.save()
        ProfilePermission.objects.create(
            profile=self.miembro_a.profile, content_type=self.ct_org, object_id=self.org_a.pk
        )
        response = self.client.get(
            reverse("auth_and_perms:api-userinorg-list"), {"organization": self.org_a.pk, "search": "miembro"}
        )
        self.assertEqual(response.json()["recordsFiltered"], 1)
