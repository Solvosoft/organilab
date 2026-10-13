"""Endpoints select2 de `auth_and_perms/gtselects.py`."""

from django.contrib.auth.models import Group, User
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from auth_and_perms.tests.escenario import EscenarioOrganizaciones
from laboratory.models import Object, OrganizationStructure, OrganizationStructureRelations, UserOrganization


class Select2Base(EscenarioOrganizaciones):
    def setUp(self):
        self.admin_a = self.crear_usuario(
            "admin-a",
            self.org_a,
            perms=["laboratory.view_laboratory", "auth.change_group"],
            ambito="perfil",
            first_name="Ada",
        )
        self.client.force_login(self.admin_a)

    def resultados(self, response):
        self.assertEqual(response.status_code, 200, response.content[:300])
        return response.json()["results"]

    def textos(self, response):
        return [r["text"] for r in self.resultados(response)]


class RolesYUsuariosTest(Select2Base):
    def test_roles_por_parametro_de_organizacion(self):
        rol = Rol.objects.get(name="Rol de admin-a")
        response = self.client.get(reverse("rolbase-list"), {"organization": self.org_a_hija.pk})
        self.assertIn(rol.name, self.textos(response))

    def test_usuarios_para_laboratorio_por_detalle(self):
        sin_perfil = User.objects.create_user("sin-perfil")
        UserOrganization.objects.create(user=sin_perfil, organization=self.org_a)
        response = self.client.get(
            reverse("laborguserbase-detail", args=[self.org_a.pk]),
            {"typeofcontenttype": "organization"},
        )
        self.assertEqual(self.resultados(response), [])

        response = self.client.get(
            reverse("laborguserbase-list"),
            {"organization": self.org_a.pk, "typeofcontenttype": "laboratory", "laboratory": self.lab_a.pk},
        )
        textos = self.textos(response)
        self.assertIn("Ada (admin-a)", textos)
        self.assertIn("sin-perfil", textos)

    def test_usuarios_para_laboratorio_con_organizacion_inactiva_o_invalida(self):
        self.org_b.active = False
        self.org_b.save()
        response = self.client.get(reverse("laborguserbase-detail", args=[self.org_b.pk]))
        self.assertEqual(response.status_code, 400)
        response = self.client.get(reverse("laborguserbase-list"), {"organization": self.org_b.pk})
        self.assertNegado(response, 404)

    def test_usuarios_de_organizacion_por_parametros(self):
        sin_perfil = User.objects.create_user("sin-perfil-2")
        UserOrganization.objects.create(user=sin_perfil, organization=self.org_a)
        response = self.client.get(
            reverse("orguserbase-list"), {"organization": self.org_a.pk, "laboratory": self.lab_a.pk}
        )
        textos = self.textos(response)
        self.assertIn("Ada", textos)
        self.assertIn(str(sin_perfil.pk), textos)

    def test_roles_como_grupos_muestran_sus_organizaciones(self):
        rol = Rol.objects.get(name="Rol de admin-a")
        self.org_a_hija.rol.add(rol)
        UserOrganization.objects.create(user=self.admin_a, organization=self.org_a_hija)
        response = self.client.get(reverse("groupbase-list"))
        texto = [t for t in self.textos(response) if "Rol de admin-a" in t][0]
        self.assertIn("Organización A -- Organización A hija", texto)
        self.assertTrue(texto.startswith(str(rol.pk)))


class LaboratoriosRelacionadosTest(Select2Base):
    def test_relorg_por_detalle_en_raiz_y_en_hija(self):
        response = self.client.get(reverse("relorgbase-detail", args=[self.org_a.pk]))
        self.assertIn("Laboratorio A", self.textos(response))
        OrganizationStructureRelations.objects.create(
            organization=self.org_a_hija, content_type=self.ct_lab, object_id=self.lab_a.pk
        )
        response = self.client.get(reverse("relorgbase-detail", args=[self.org_a_hija.pk]))
        self.assertNotIn("Laboratorio A", self.textos(response))

    def test_relorg_por_parametro_y_sin_organizacion(self):
        response = self.client.get(reverse("relorgbase-list"), {"organization": self.org_a.pk})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("relorgbase-list"), {"organization": "x"})
        self.assertNegado(response, 404)

    def test_relorgfull_con_grupo_de_registro_usa_las_relaciones_de_la_raiz(self):
        grupo, _ = Group.objects.get_or_create(name="RegisterOrganization")
        self.admin_a.groups.add(grupo)
        OrganizationStructureRelations.objects.create(
            organization=self.org_a, content_type=self.ct_lab, object_id=self.lab_a.pk
        )
        # La hija hereda los laboratorios relacionados con la raíz...
        response = self.client.get(reverse("relorgfullbase-detail", args=[self.org_a_hija.pk]))
        self.assertEqual(self.textos(response), ["Laboratorio A"])
        # ...pero la propia raíz ya lo tiene vinculado y no se le vuelve a ofrecer.
        response = self.client.get(reverse("relorgfullbase-detail", args=[self.org_a.pk]))
        self.assertEqual(self.resultados(response), [])

    def test_relorgfull_por_parametro(self):
        response = self.client.get(reverse("relorgfullbase-list"), {"organization": self.org_a.pk})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("relorgfullbase-list"), {"organization": "x"})
        self.assertNegado(response, 404)

    def test_laborg_por_detalle(self):
        response = self.client.get(reverse("laborgbase-detail", args=[self.org_a.pk]))
        self.assertEqual(self.textos(response), ["Laboratorio A"])
        self.org_a_hija.active = False
        self.org_a_hija.save()
        response = self.client.get(reverse("laborgbase-detail", args=[self.org_a_hija.pk]))
        self.assertEqual(response.status_code, 400)

    def test_laborg_con_parametros_invalidos(self):
        response = self.client.get(reverse("laborgbase-list"), {"organization": self.org_a.pk, "laboratory": "x"})
        self.assertEqual(response.status_code, 400)


class OrganizacionesYPerfilesTest(Select2Base):
    def test_organizaciones_del_usuario_marcan_al_padre(self):
        UserOrganization.objects.create(user=self.admin_a, organization=self.org_a_hija)
        response = self.client.get(reverse("orgbyuser-list"), {"org": self.org_a_hija.pk})
        ids = [r["id"] for r in self.resultados(response)]
        self.assertNotIn(self.org_a_hija.pk, ids)
        seleccionados = [r for r in self.resultados(response) if r.get("selected")]
        self.assertEqual([r["id"] for r in seleccionados], [self.org_a.pk])

    def test_grupos_por_perfil_invalido(self):
        response = self.client.get(reverse("groupsbyprofile-list"), {"profile": 999999})
        self.assertEqual(response.status_code, 400)
        self.assertIn("profile", response.json()["errors"])

    def test_usuarios_por_organizacion(self):
        sin_nombre = self.crear_usuario("sin-nombre", self.org_a)
        response = self.client.get(reverse("usersbyorg-list"), {"organization": self.org_a.pk})
        textos = self.textos(response)
        self.assertIn("sin-nombre", textos)
        self.assertTrue(any(t.startswith("Ada") for t in textos))
        response = self.client.get(reverse("usersbyorg-list"), {"organization": 999999})
        self.assertNegado(response, 404)
        self.assertTrue(sin_nombre)

    def test_arbol_de_organizaciones_para_superusuario(self):
        su = User.objects.create_superuser("raiz", "raiz@ejemplo.cr", "clave")
        Profile.objects.create(user=su)
        UserOrganization.objects.create(user=su, organization=self.org_a)
        UserOrganization.objects.create(user=su, organization=self.org_a_hija)
        self.client.force_login(su)
        response = self.client.get(reverse("orgtree-list"))
        self.assertEqual(
            self.textos(response),
            ["%d | Organización A" % self.org_a.pk, "-- %d | Organización A hija" % self.org_a_hija.pk],
        )

    def test_arbol_con_rol_administrativo_superior(self):
        rol = Rol.objects.create(name="Administrativo superior")
        pp = ProfilePermission.objects.create(
            profile=self.admin_a.profile, content_type=self.ct_org, object_id=self.org_a.pk
        )
        pp.rol.add(rol)
        response = self.client.get(reverse("orgtree-list"))
        self.assertIn("%d | Organización A" % self.org_a.pk, self.textos(response))

    def test_objetos_por_organizacion_invalida(self):
        Object.objects.create(code="OBJ-1", name="Acetona", organization=self.org_a, type=Object.REACTIVE)
        response = self.client.get(reverse("objbyorg-list"), {"organization": 999999})
        self.assertNegado(response, 404)
        self.assertTrue(OrganizationStructure.objects.filter(pk=self.org_a.pk).exists())
