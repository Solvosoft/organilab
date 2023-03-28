import json

from django.urls import reverse

from auth_and_perms.models import ProfilePermission
from laboratory.tests.utils import BaseOrganizatonManageSetUpTest


class OrganizationViewTest(BaseOrganizatonManageSetUpTest):

    def test_check_user1_append_rol_to_profile(self):
        """
        Usuario 1 agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org2.pk})
        self.base_data.update({
            'mergeaction': 'append',
            'profile': self.profile_org2.pk,
        })
        response = self.client_org1.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertFalse(self.role_manage_lab in pp.rol.all())
        self.assertFalse(self.org2 in self.user1_org_list)

    def test_check_user2_append_rol_to_profile(self):
        """
        Usuario 2 agregando 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab3_org2.pk})
        self.base_data.update({
            'mergeaction': 'append',
            'profile': self.profile_org2.pk,
        })
        response = self.client_org2.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertTrue(self.role_manage_lab in pp.rol.all())
        self.assertTrue(self.org2 in self.user2_org_list)

    def test_check_user1_sustract_rol_to_profile(self):
        """
        Usuario 1 sustrayendo 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        self.base_data.update({
            'mergeaction': 'sustract',
            'profile': self.profile_org2.pk,
        })
        response = self.client_org1.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertFalse(not self.role_manage_lab in pp.rol.all())
        self.assertFalse(self.org2 in self.user1_org_list)

    def test_check_user2_sustract_rol_to_profile(self):
        """
        Usuario 2 sustrayendo 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org2.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org2.pk, 'objectid': self.lab4_org2.pk})
        self.base_data.update({
            'mergeaction': 'sustract',
            'profile': self.profile_org2.pk,
        })
        response = self.client_org2.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org2,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertTrue(not self.role_manage_lab in pp.rol.all())
        self.assertTrue(self.org2 in self.user2_org_list)

    def test_check_user2_full_rol_to_profile(self):
        """
        Usuario 2 sustrayendo roles y agregando 1 rol(Gestión lab) en una org de la cual NO es miembro, CASO NO PERMITIDO DEBERIA FALLAR
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org1.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org1.pk, 'objectid': self.lab1_org1.pk})
        self.base_data.update({
            'mergeaction': 'full',
            'profile': self.profile_org1.pk,
        })
        response = self.client_org2.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertNotEqual(pp.rol.all().count(), len(self.base_data['rols']))
        self.assertFalse(self.role_manage_lab in pp.rol.all())
        self.assertTrue(self.org1 in self.user2_org_list)

    def test_check_user1_full_rol_to_profile(self):
        """
        Usuario 1 sustrayendo roles y agregando 1 rol(Gestión lab) en una org de la cual SI es miembro, CASO PERMITIDO
        """

        url = reverse("auth_and_perms:api-rolbyorg-detail", kwargs={"pk": self.org1.pk, })
        self.base_data['contenttypeobj'].update({'org': self.org1.pk, 'objectid': self.lab1_org1.pk})
        self.base_data.update({
            'mergeaction': 'full',
            'profile': self.profile_org1.pk,
        })
        response = self.client_org1.put(url, data=json.dumps(self.base_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        pp = ProfilePermission.objects.filter(profile=self.profile_org1,
                                              content_type=self.lab_contenttype,
                                              object_id=self.base_data['contenttypeobj']['objectid']).first()
        self.assertEqual(pp.rol.all().count(), len(self.base_data['rols']))
        self.assertTrue(self.role_manage_lab in pp.rol.all())
        self.assertTrue(self.org1 in self.user1_org_list)