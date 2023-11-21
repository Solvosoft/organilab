from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import json

from django_otp.plugins.otp_totp.models import TOTPDevice

from auth_and_perms.models import Rol, RegistrationUser, UserTOTPDevice
from laboratory.models import UserOrganization, OrganizationStructure, OrganizationStructureRelations


class OrganizationTest(TestCase):
    fixtures = ['auth.json']
    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_get_select_organization(self):

        response = self.client.get(reverse('auth_and_perms:select_organization_by_user'))
        self.assertEqual(response.status_code, 200)

    def test_add_user_organization(self):
        """
        Esta prueba agrega un usuario que ya existe en la organización, por lo que no se debería modificar nada
        """
        data = {
            'users': [1]
        }

        pre_user_org = UserOrganization.objects.get(user__pk=1, organization__pk=1).status

        response = self.client.post(reverse('auth_and_perms:addusersorganization', kwargs={'pk':1}),data=data)

        self.assertEqual(response.status_code, 302)
        pos_user_org = UserOrganization.objects.get(user__pk=1, organization__pk=1).status

        self.assertTrue(pos_user_org)
        self.assertTrue(pos_user_org == pre_user_org)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response, success_url)


    def test_remove_user_organization(self):

        data = {
            'users': []
        }

        pre_user_org = UserOrganization.objects.get(user__pk=1, organization__pk=1,
                                                    type_in_organization=1).status

        response = self.client.post(reverse('auth_and_perms:addusersorganization', kwargs={'pk':1}),data=data)

        self.assertEqual(response.status_code, 302)
        pos_user_org = UserOrganization.objects.filter(user__pk=1, organization__pk=1).count()

        # return 0 how is false
        self.assertFalse(pos_user_org)
        #self.assertTrue(pos_user_org!=pre_user_org)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response, success_url)

    def test_user_organization_error_pk(self):

        response = self.client.get(reverse('auth_and_perms:addusersorganization', kwargs={'pk':1}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(_("Organization doesn't exists") == str(list(get_messages(response.wsgi_request))[0]))

    def test_list_user_organization(self):

        response = self.client.get(reverse('auth_and_perms:organizationManager'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['nodes'])>0)

    def test_adduser_organization(self):
        data = {
            'username':'Lola',
            'first_name':'Vaca',
            'last_name':'Lola',
            'email':'lola@vaca.ac.cr',
            'phone_number':'6666-66-66',
            'id_card': '1331113',
            'job_position': 'Lechera'
        }
        pre_org = UserOrganization.objects.filter(organization__pk=1).count()
        response = self.client.post(reverse('auth_and_perms:add_user', kwargs={'pk':1}),data=data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.last()
        user_org = UserOrganization.objects.filter(user=user, organization__pk=1).first()
        post_org = UserOrganization.objects.filter(organization__pk=1).count()
        self.assertIsNotNone(user_org)
        self.assertTrue(post_org > pre_org)
        self.assertTrue(_("Element saved successfully")== str(list(get_messages(response.wsgi_request))[0]))
        self.assertRedirects(response, reverse('auth_and_perms:organizationManager'))

    def test_list_rol_organization(self):

        response = self.client.get(reverse('auth_and_perms:list_rol_by_org', kwargs={'org_pk':1}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['object_list'].count()>0)
        self.assertIsNotNone(response.context['object_list'])

    def test_list_rol_organization_unknown_pk(self):

        response = self.client.get(reverse('auth_and_perms:list_rol_by_org', kwargs={'org_pk':14}))
        self.assertEqual(response.status_code, 404)
        #self.assertTrue(response.context['object_list'].count()==0)

    def test_delete_rol_organization(self):
        get_response = self.client.get(reverse('auth_and_perms:del_rol_by_org', kwargs={'org_pk':1,'pk':1}))

        pre_rol = OrganizationStructure.objects.get(pk=1).rol.count()

        post_response = self.client.post(reverse('auth_and_perms:del_rol_by_org', kwargs={'org_pk':1,'pk':1}))
        pos_rol = OrganizationStructure.objects.get(pk=1).rol.count()
        rol = Rol.objects.filter(pk=1).first()


        self.assertEqual(post_response.status_code, 302)
        self.assertContains(get_response, 'Gestión de Organizaciones')
        success_url = reverse('auth_and_perms:list_rol_by_org', args=[1])
        self.assertRedirects(post_response, success_url)
        self.assertTrue(pre_rol > pos_rol)
        self.assertIsNone(rol)

    def test_copy_rols(self):

        data = {
            'org_pk':1,
            'rols': [3]
        }
        pre_rol = OrganizationStructure.objects.get(pk=1).rol.count()
        post_response = self.client.post(reverse('auth_and_perms:copy_rols', kwargs={'pk':1}), data=data)
        self.assertEqual(post_response.status_code, 302)
        pos_rol = OrganizationStructure.objects.get(pk=1).rol.count()
        success_url = reverse('auth_and_perms:organizationManager')
        self.assertTrue(_("Element saved successfully") == str(list(get_messages(post_response.wsgi_request))[0]))

        self.assertRedirects(post_response, success_url)
        self.assertTrue(pos_rol > pre_rol)

    def test_copy_rols_error(self):
        data = {
            'org_pk':1,
        }
        pre_rol = OrganizationStructure.objects.get(pk=1).rol.count()

        post_response = self.client.post(reverse('auth_and_perms:copy_rols', kwargs={'pk':1}), data=data)
        pos_rol = OrganizationStructure.objects.get(pk=1).rol.count()


        self.assertEqual(post_response.status_code, 302)
        success_url = reverse('auth_and_perms:organizationManager')
        self.assertTrue(_("Error, form is invalid") == str(list(get_messages(post_response.wsgi_request))[0]))
        self.assertRedirects(post_response, success_url)
        self.assertTrue(pos_rol == pre_rol)

    def test_add_contenttype_to_org(self):
        data = {
            'organization': 1,
            'contentyperelobj':[1, 2]
        }
        org_relacion= OrganizationStructureRelations.objects.all().count() # No rel on auth.json
        response = self.client.post(reverse('auth_and_perms:add_contenttype_to_org'),data=data)
        org_relations= OrganizationStructureRelations.objects.filter(organization=1).count() # 2

        self.assertEqual(response.status_code, 302)
        self.assertTrue(org_relations==2)
        self.assertRedirects(response, reverse('auth_and_perms:organizationManager'))

    def test_add_contenttype_to_org_not_lab(self):
        data = {
            'organization': 1,
            'contentyperelobj':[]
        }
        org_relacion= OrganizationStructureRelations.objects.all().count()
        response = self.client.post(reverse('auth_and_perms:add_contenttype_to_org'),data=data)
        org_relations= OrganizationStructureRelations.objects.filter(organization__pk=1)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(org_relations.count() == 0)
        #self.assertRedirects(response, reverse('auth_and_perms:organizationManager'))

    def test_add_contenttype_to_org_error(self):
        data = {
            'organization': 999,
            'contentyperelobj':[37]
        }
        response = self.client.post(reverse('auth_and_perms:add_contenttype_to_org'),data=data)
        org_relations= OrganizationStructureRelations.objects.filter(organization__pk=1)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(org_relations.count() == 0)

    def test_register_user_digital(self):
        data = {
             'username' :"p@gmail.co",
             'validation_method' : 2,
             'organization_name' : "CR Full",
             'password1' : "112153153fas",
             'password2': "112153153fas",
        }
        response = self.client.post(reverse('auth_and_perms:register_user_to_platform'), data=data)
        user = User.objects.last()
        user_regist= RegistrationUser.objects.filter(user=user)
        success_url =reverse('auth_and_perms:create_profile_by_digital_signature', kwargs={'pk':user.pk})

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(response, success_url)
        self.assertTrue(user_regist.count()==1)

    def test_register_user_otp(self):
        data = {
             'username' :"p@gmail.co",
             'validation_method' : 1,
             'organization_name' : "CR Full",
             'password1' : "112153153fas",
             'password2': "112153153fas",
        }
        response = self.client.post(reverse('auth_and_perms:register_user_to_platform'), data=data)
        user = User.objects.last()
        user_regist= RegistrationUser.objects.filter(user=user)
        success_url =reverse('auth_and_perms:user_org_creation_totp', kwargs={'pk':user.pk})
        otp = UserTOTPDevice.objects.filter(user=user).count()
        self.assertEqual(response.status_code, 302)

        self.assertRedirects(response, success_url)
        self.assertTrue(user_regist.count()==1)
        self.assertTrue(otp==1)

    def test_register_user_error(self):
        data = {
             'username' :"pgmail.co",
             'validation_method' : 0,
             'organization_name' : "CR Full",
             'password1' : "112153153fas",
             'password2': "112153153fas",
        }
        response = self.client.post(reverse('auth_and_perms:register_user_to_platform'), data=data)
        user = User.objects.last()
        user_regist= RegistrationUser.objects.filter(user=user)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(user_regist.count()==0)

    def test_rol_list(self):

        url = reverse("auth_and_perms:api-rol-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['count'] >0)
        self.assertContains(response,'permissions')

    def test_add_rol(self):
        data = {
            "name": "Limpieza",
            "color": "#003001",
            "permissions":[7,30,4],
            "rol": 1,
            "relate_rols": [1, 2],
        }
        url = reverse("auth_and_perms:api-rol-list")
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(data['name'], json.loads(response.content)['name'])

