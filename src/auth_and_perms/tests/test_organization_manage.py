import json

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import ProfilePermission
from laboratory.tests.utils import BaseOrganizatonManageSetUpTest


class ActionRolViewTest(BaseOrganizatonManageSetUpTest):

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

    def test_check_user1_append_rol_to_profile(self):
        """
        Usuario 1 agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        data = self.base_data
        data.update({'mergeaction': 'append', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org1.pk})
        response = self.client1_org1.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.role_manage_lab in pp.rol.all())

    def test_check_user2_append_rol_to_profile(self):
        """
        Usuario 2 agregando 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        data = self.base_data
        data.update({'mergeaction': 'append', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org1.pk})
        response = self.client2_org2.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.role_manage_lab in pp.rol.all())

    def test_check_user1_sustract_rol_to_profile(self):
        """
        Usuario 1 sustrayendo 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        data = self.base_data
        data.update({'mergeaction': 'sustract', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        response = self.client1_org1.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(not self.role_manage_lab in pp.rol.all())

    def test_check_user2_sustract_rol_to_profile(self):
        """
        Usuario 2 sustrayendo 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        data = self.base_data
        data.update({'mergeaction': 'sustract', 'profile': self.profile2_org2.pk})
        data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        response = self.client2_org2.put(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile2_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['contenttypeobj']['objectid']).first()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(not self.role_manage_lab in pp.rol.all())

    def test_check_user2_full_rol_to_profile(self):
        """
        Usuario 2 sustrayendo roles y agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org1.pk, })
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

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org1.pk, })
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

class DeleteProfilePermissionLabViewTest(BaseOrganizatonManageSetUpTest):

    def setUp(self):
        super().setUp()
        self.lab = self.lab1_org1
        self.org = self.lab.organization
        self.base_data = {
            'app_label': self.lab._meta.app_label,
            'model': self.lab._meta.model_name,
            'disable_user': False
        }

    def test_user1_delete_profilepermissionslab1profile3(self):
        """
        Usuario 1 elimina profilepermission lab 1 perfil 3 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-deluserorgcontt-list")
        data = self.base_data
        data.update({
            'object_id': self.lab.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })
        response = self.client1_org1.delete(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pp.exists())

    def test_user2_delete_profilepermissionslab1profile3(self):
        """
        Usuario 2 elimina profilepermission lab 1 perfil 3 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-deluserorgcontt-list")
        data = self.base_data
        data.update({
            'object_id': self.lab.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org.pk,
        })
        response = self.client2_org2.delete(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 403)
        self.assertTrue(pp.exists())

class CreateProfilePermissionLabViewTest(BaseOrganizatonManageSetUpTest):

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

    def test_user1_create_profilepermissionslab2user4(self):
        """
        Usuario 1 crea profilepermission lab 2 perfil 4 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-relusertocontenttype-list")
        data = self.base_data
        response = self.client1_org1.post(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['laboratory'])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(pp.exists())

    def test_user2_create_profilepermissionslab2user4(self):
        """
        Usuario 1 crea profilepermission lab 2 perfil 4 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-relusertocontenttype-list")
        data = self.base_data
        response = self.client2_org2.post(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=data['laboratory'])
        self.assertEqual(response.status_code, 201)
        self.assertTrue(pp.exists())

class DeleteProfilePermissionOrgViewTest(BaseOrganizatonManageSetUpTest):

    def setUp(self):
        super().setUp()
        self.base_data = {
            'app_label': 'laboratory',
            'model': 'organizationstructure',
            'disable_user': False
        }

    def test_user1_delete_profilepermissionsorg1profile3(self):
        """
        Usuario 1 elimina profilepermission org 1 lab 3 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-deluserorgcontt-list")
        data = self.base_data
        data.update({
            'object_id': self.org1.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org1.pk,
        })
        response = self.client1_org1.delete(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pp.exists())

    def test_user2_delete_profilepermissionsorg1profile3(self):
        """
        Usuario 2 elimina profilepermission org 1 perfil 3 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-deluserorgcontt-list")
        data = self.base_data
        data.update({
            'object_id': self.org1.pk,
            'profile': self.profile3_org1.pk,
            'organization': self.org1.pk,
        })
        response = self.client2_org2.delete(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile3_org1,
                                              content_type=self.org_contenttype,
                                              object_id=data['object_id'])
        self.assertEqual(response.status_code, 403)
        self.assertTrue(pp.exists())

class CreateProfilePermissionOrgViewTest(BaseOrganizatonManageSetUpTest):

    def setUp(self):
        super().setUp()
        self.org = self.org2
        self.base_data = {
            'typeofcontenttype': 'organization',
            'user': self.user4_org2.pk,
            'organization': self.org.pk
        }

    def test_user1_create_profilepermissionsorg2user4(self):
        """
        Usuario 1 crea profilepermission org 2 perfil 4 en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-relusertocontenttype-list")
        data = self.base_data
        response = self.client1_org1.post(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.org_contenttype,
                                              object_id=data['organization'])
        self.assertEqual(response.status_code, 403)
        self.assertFalse(pp.exists())

    def test_user2_create_profilepermissionsorg2user4(self):
        """
        Usuario 2 crea profilepermission org 2 perfil 4 en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-relusertocontenttype-list")
        data = self.base_data
        response = self.client2_org2.post(url, data=json.dumps(data), content_type='application/json')
        pp = ProfilePermission.objects.filter(profile=self.profile4_org2,
                                              content_type=self.org_contenttype,
                                              object_id=data['organization'])
        self.assertEqual(response.status_code, 201)
        self.assertTrue(pp.exists())