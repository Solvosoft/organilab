import json

from django.urls import reverse

from auth_and_perms.models import ProfilePermission, Profile, Rol
from laboratory.models import UserOrganization
from laboratory.tests.utils import BaseSetUpAjaxRequest, BaseSetUpDjangoRequest
from laboratory.utils import get_profile_by_organization


class ActionRolViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.base_data = {
            'rols': [self.role_manage_lab.pk],
            'as_role': True,
            'as_user': False,         # REMOVE
            'as_conttentype': False,  # REMOVE
            'contenttypeobj': {
                'model': 'laboratory',
                'appname': 'laboratory'
            },
        }
        self.url_name = "auth_and_perms:api-rolbyorg-detail"
        self.url = reverse(self.url_name, kwargs={"pk": self.org2.pk, })

    def test_check_user1_append_rol_to_profile(self):
        """
        Usuario 1 agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({'mergeaction': 'append', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org1.pk})
        response = self.client1_org1.put(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.role_manage_lab in pp.rol.all())

    def test_check_user2_append_rol_to_profile(self):
        """
        Usuario 2 agregando 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({'mergeaction': 'append', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org1.pk})
        response = self.client2_org2.put(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.role_manage_lab in pp.rol.all())

    def test_check_user1_sustract_rol_to_profile(self):
        """
        Usuario 1 sustrayendo 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({'mergeaction': 'sustract', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        response = self.client1_org1.put(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(not self.role_manage_lab in pp.rol.all())

    def test_check_user2_sustract_rol_to_profile(self):
        """
        Usuario 2 sustrayendo 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({'mergeaction': 'sustract', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        response = self.client2_org2.put(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not self.role_manage_lab in pp.rol.all())

    def test_check_user2_full_rol_to_profile(self):
        """
        Usuario 2 sustrayendo roles y agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse(self.url_name, kwargs={"pk": self.org1.pk, })
        data = self.base_data
        data.update({'mergeaction': 'full', 'profile': self.profile1_org1.pk})
        data['contenttypeobj'].update({'org': self.org1.pk, 'objectid': self.lab1_org1.pk})
        response = self.client2_org2.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile1_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(pp.rol.all().count(), len(data['rols']))
        self.assertFalse(self.role_manage_lab in pp.rol.all())

    def test_check_user1_full_rol_to_profile(self):
        """
        Usuario 1 sustrayendo roles y agregando 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse(self.url_name, kwargs={"pk": self.org1.pk, })
        data = self.base_data
        data.update({'mergeaction': 'full', 'profile': self.profile1_org1.pk})
        data['contenttypeobj'].update({'org': self.org1.pk, 'objectid': self.lab1_org1.pk})
        response = self.client1_org1.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile1_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pp.rol.all().count(), len(data['rols']))
        self.assertTrue(self.role_manage_lab in pp.rol.all())

class DeleteProfilePermissionLabViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab1_org1
        self.org = self.lab.organization
        self.base_data = {
            'app_label': self.lab._meta.app_label,
            'model': self.lab._meta.model_name,
            'disable_user': False
        }
        self.url = reverse("auth_and_perms:api-deluserorgcontt-list")

    def test_user1_delete_profilepermissionslab1profile3(self):
        """
        Usuario 1 elimina profilepermission lab 1 perfil 3 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({
            'object_id': self.lab.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })

        # VERIFICAR QUE EXISTE EL ELEMENTO ANTES DE SER ELIMINADO
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertTrue(pp.exists())

        response = self.client1_org1.delete(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pp.exists())

    def test_user2_delete_profilepermissionslab1profile3(self):
        """
        Usuario 2 elimina profilepermission lab 1 perfil 3 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({
            'object_id': self.lab.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })

        # VERIFICAR QUE EXISTE EL ELEMENTO ANTES DE SER ELIMINADO
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertTrue(pp.exists())

        response = self.client2_org2.delete(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 403)
        self.assertTrue(pp.exists())

class CreateProfilePermissionLabViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.org = self.lab.organization
        self.base_data = {
            'typeofcontenttype': 'laboratory',
            'user': self.user4_org2.pk,
            'laboratory': self.lab.pk,
            'organization': self.org.pk
        }
        self.url = reverse("auth_and_perms:api-relusertocontenttype-list")

    def test_user1_create_profilepermissionslab2user4(self):
        """
        Usuario 1 crea profilepermission lab 2 perfil 4 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        response = self.client1_org1.post(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['laboratory'])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(pp.exists())

    def test_user2_create_profilepermissionslab2user4(self):
        """
        Usuario 1 crea profilepermission lab 2 perfil 4 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        response = self.client2_org2.post(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['laboratory'])
        self.assertEqual(response.status_code, 201)
        self.assertTrue(pp.exists())

class ListProfileLabViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab1_org1
        self.org = self.lab.organization
        self.base_data = {
            'organization': self.org.pk,
            'laboratory': self.lab.pk
        }
        self.profiles = self.get_queryset()
        self.url = reverse("auth_and_perms:api-prolaborg-list")

    def get_queryset(self):
        profiles = get_profile_by_organization(self.org.pk)
        return profiles.filter(
            profilepermission__content_type__app_label=self.lab._meta.app_label,
            profilepermission__content_type__model=self.lab._meta.model_name,
            profilepermission__object_id=self.lab.pk)

    def test_user2_list_profileslab1_set_limit(self):
        """
        Usuario 2 obtiene la lista de perfiles del lab 1 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({'offset': 0, 'limit': 10})
        response = self.client2_org2.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.profiles.count(), len(response_data))
        self.assertNotContains(response, self.profiles.first().user.get_full_name())

    def test_user2_list_profileslab1_default_limit(self):
        """
        Usuario 2 obtiene la lista de perfiles del lab 1 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        response = self.client2_org2.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.profiles.count(), len(response_data))
        self.assertNotContains(response, self.profiles.first().user.get_full_name())

    def test_user1_list_profileslab1_set_limit(self):
        """
        Usuario 1 obtiene la lista de profilepermission del lab 1 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({'offset': 0, 'limit': 10})
        response = self.client1_org1.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.profiles.count(), len(response_data))
        self.assertContains(response, self.profiles.first().user.get_full_name())

    def test_user1_list_profileslab1_default_limit(self):
        """
        Usuario 1 obtiene la lista de profilepermission del lab 1 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        response = self.client1_org1.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.profiles.count(), len(response_data))
        self.assertContains(response, self.profiles.first().user.get_full_name())

class DeleteProfilePermissionOrgViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.base_data = {
            'app_label': 'laboratory',
            'model': 'organizationstructure',
            'disable_user': False
        }
        self.url = reverse("auth_and_perms:api-deluserorgcontt-list")

    def test_user1_delete_profilepermissionsorg1profile3(self):
        """
        Usuario 1 elimina profilepermission3 org 1 de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({
            'object_id': self.org.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })

        #VERIFICAR QUE EXISTE EL ELEMENTO ANTES DE SER ELIMINADO
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertTrue(pp.exists())

        response = self.client1_org1.delete(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pp.exists())
        self.assertFalse(UserOrganization.objects.filter(organization=self.org, user=self.profile3_org1.user).exists())
        if self.orgum:
            self.assertFalse(self.orgum.users.filter(profile=self.profile3_org1).exists())

    def test_user2_delete_profilepermissionsorg1profile3(self):
        """
        Usuario 2 elimina profilepermission3 org 1 la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({
            'object_id': self.org.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })

        # VERIFICAR QUE EXISTE EL ELEMENTO ANTES DE SER ELIMINADO
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertTrue(pp.exists())

        response = self.client2_org2.delete(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 403)
        self.assertTrue(pp.exists())
        self.assertTrue(UserOrganization.objects.filter(organization=self.org, user=self.profile3_org1.user).exists())
        if self.orgum:
            self.assertTrue(self.orgum.users.filter(profile=self.profile3_org1).exists())

class CreateProfilePermissionOrgViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.org = self.org2
        self.base_data = {
            'typeofcontenttype': 'organization',
            'user': self.user4_org2.pk,
            'organization': self.org.pk
        }
        self.url = reverse("auth_and_perms:api-relusertocontenttype-list")

    def test_user1_create_profilepermissionsorg2user4(self):
        """
        Usuario 1 crea profilepermission org 2 perfil 4 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        response = self.client1_org1.post(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.org_contenttype,
                                              object_id=data['organization'])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(pp.exists())

    def test_user2_create_profilepermissionsorg2user4(self):
        """
        Usuario 2 crea profilepermission org 2 perfil 4 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        response = self.client2_org2.post(self.url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.org_contenttype,
                                              object_id=data['organization'])
        self.assertEqual(response.status_code, 201)
        self.assertTrue(pp.exists())

class ListProfileOrgViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.org = self.org2
        self.base_data = {
            'organization': self.org.pk,
        }
        self.profiles = self.get_queryset()
        self.url = reverse("auth_and_perms:api-userinorg-list")

    def get_queryset(self):
        queryset = Profile.objects.all()
        profiles = queryset.filter(user__in=self.org.values_list('users', flat=True))

        return profiles.filter(
            profilepermission__content_type__app_label=self.org._meta.app_label,
            profilepermission__content_type__model=self.org._meta.model_name,
            profilepermission__object_id=self.org.pk).order_by('-user')

    def test_user1_list_profilesorg2_set_limit(self):
        """
        Usuario 1 obtiene la lista de perfiles de la org2 de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        data.update({'offset': 0, 'limit': 10})
        response = self.client1_org1.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.profiles.count(), len(response_data))
        self.assertNotContains(response, self.profiles.first().user.get_full_name())

    def test_user1_list_profilesorg2_default_limit(self):
        """
        Usuario 1 obtiene la lista de perfiles de la org2 de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        data = self.base_data
        response = self.client1_org1.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(self.profiles.count(), len(response_data))
        self.assertNotContains(response, self.profiles.first().user.get_full_name())

    def test_user2_list_profilesorg2_set_limit(self):
        """
        Usuario 2 obtiene la lista de perfiles de la org2 de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        data.update({'offset': 0, 'limit': 10})
        response = self.client2_org2.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.profiles.count(), len(response_data))
        self.assertContains(response, self.profiles.first().user.get_full_name())

    def test_user2_list_profilesorg2_default_limit(self):
        """
        Usuario 2 obtiene la lista de perfiles de la org2 de la cual SI es miembro, CASO PERMITIDO
        """

        data = self.base_data
        response = self.client2_org2.get(self.url, data=data)
        response_data = json.loads(response.content)['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.profiles.count(), len(response_data))
        self.assertContains(response, self.profiles.first().user.get_full_name())

class CreateRolViewTest(BaseSetUpAjaxRequest):

    def setUp(self):
        super().setUp()
        self.url = reverse("auth_and_perms:api-rol-list")

    def test_user1_create_rol_org1_with_relaterols(self):
        """
        Usuario 1 crea rol con roles relacionados(copiado de permisos) de la org1 de la cual SI es miembro, CASO PERMITIDO
        """

        data = {
            'name': "Gestión de reportes",
            'relate_rols': [1, 2],
            'rol': self.org1.pk,
        }
        response = self.client1_org1.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(data['name'], json.loads(response.content)['name'])

    def test_user1_create_rol_org1_without_relaterols(self):
        """
        Usuario 1 crea rol sin roles relacionados(copiado de permisos) de la org1 de la cual SI es miembro, CASO PERMITIDO
        """

        data = {
            'name': "Gestión de sustancias",
            'rol': self.org1.pk,
        }
        response = self.client1_org1.post(self.url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(data['name'], json.loads(response.content)['name'])

    def test_user2_create_rol_org1_with_relaterols(self):
        """
        Usuario 2 crea rol con roles relacionados(copiado de permisos) de la org1 de la cual NO es miembro, CASO NO PERMITIDO
        """

        data = {
            'name': "Gestión de reservaciones",
            'relate_rols': [1, 2],
            'rol': self.org1.pk,
        }
        response = self.client2_org2.post(self.url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(data['name'], json.loads(response.content)['name'])

    def test_user2_create_rol_org1_without_relaterols(self):
        """
        Usuario 2 crea rol sin roles relacionados(copiado de permisos) de la org1 de la cual NO es miembro, CASO NO PERMITIDO
        """

        data = {
            'name': "Revisión de sustancias",
            'rol': self.org1.pk,
        }
        response = self.client2_org2.post(self.url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(data['name'], json.loads(response.content)['name'])

class User1DeleteRolViewTest(BaseSetUpDjangoRequest):

    def setUp(self):
        super().setUp()
        # CLIENT - LOGIN
        self.client1_org1 = self.client
        self.client1_org1.force_login(self.user1_org1)
        self.rol = Rol.objects.get(name='Gestión de reporte de zonas de riesgo')
        self.url = reverse("auth_and_perms:del_rol_by_org", kwargs={'org_pk': self.org.pk, 'pk': self.rol.pk})

    def test_user1_delete_rol_org3(self):
        """
        Usuario 1 elimina rol de la org3 de la cual SI es miembro, CASO PERMITIDO
        """

        #VERIFICAR QUE EL ROL EXISTA ANTES DE SER ELIMINADO DE LA ORG
        org_rol_check = self.org.rol.filter(pk=self.rol.pk)
        self.assertTrue(org_rol_check.exists())

        response = self.client1_org1.post(self.url)
        org_rol_check = self.org.rol.filter(pk=self.rol.pk)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(org_rol_check.exists())

class User2DeleteRolViewTest(BaseSetUpDjangoRequest):

    def setUp(self):
        super().setUp()
        # CLIENT - LOGIN
        self.client2_org2 = self.client
        self.client2_org2.force_login(self.user2_org2)
        self.rol = Rol.objects.get(name='Reporte de zonas de riesgo')
        self.url = reverse("auth_and_perms:del_rol_by_org", kwargs={'org_pk': self.org.pk, 'pk': self.rol.pk})

    def test_user2_delete_rol_org3(self):
        """
        Usuario 2 intenta eliminar el rol de la org3 de la cual NO es miembro, CASO NO PERMITIDO(NO DEBERIA FALLAR)
        """

        # VERIFICAR QUE EL ROL EXISTA ANTES DE SER ELIMINADO DE LA ORG
        org_rol_check = self.org.rol.filter(pk=self.rol.pk)
        self.assertTrue(org_rol_check.exists())

        response = self.client2_org2.post(self.url)
        org_rol_check = self.org.rol.filter(pk=self.rol.pk)

        #REDIRECIONA AL USER 2 QUE NO TIENE PERMISOS PARA ELIMINAR UN ROL DE UNA ORG DE LA CUAL NO ES MIEMBRO
        self.assertEqual(response.status_code, 302)
        self.assertTrue(org_rol_check.exists())