from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import json

from auth_and_perms.models import Rol
from laboratory.models import UserOrganization, OrganizationStructure, OrganizationStructureRelations


class OrganizationTest(TestCase):
    fixtures = ['auth.json']
    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=19)
        self.client.force_login(self.user)

    def test_get_select_organization(self):

        response = self.client.get(reverse('auth_and_perms:select_organization_by_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_nodes']>0)

    def test_add_user_organization(self):

        data = {
            'users': [19]
        }

        pre_user_org = UserOrganization.objects.get(user__pk=19, organization__pk=2).status

        response = self.client.post(reverse('auth_and_perms:addusersorganization', kwargs={'pk':2}),data=data)

        self.assertEqual(response.status_code, 302)
        pos_user_org = UserOrganization.objects.get(user__pk=19, organization__pk=2).status

        self.assertTrue(pos_user_org)
        self.assertTrue(pos_user_org!=pre_user_org)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response, success_url)


    def test_remove_user_organization(self):

        data = {
            'users': []
        }

        pre_user_org = UserOrganization.objects.get(user__pk=19, organization__pk=1).status

        response = self.client.post(reverse('auth_and_perms:addusersorganization', kwargs={'pk':1}),data=data)

        self.assertEqual(response.status_code, 302)
        pos_user_org = UserOrganization.objects.get(user__pk=19, organization__pk=2).status

        self.assertTrue(_("Element saved successfully") == str(list(get_messages(response.wsgi_request))[0]))
        self.assertTrue(pos_user_org==False)
        self.assertTrue(pos_user_org!=pre_user_org)
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
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['object_list'].count()==0)

    def test_delete_rol_organization(self):
        get_response = self.client.get(reverse('auth_and_perms:del_rol_by_org', kwargs={'org_pk':1,'pk':1}))

        pre_rol = OrganizationStructure.objects.get(pk=1).rol.count()

        post_response = self.client.post(reverse('auth_and_perms:del_rol_by_org', kwargs={'org_pk':1,'pk':1}))
        pos_rol = OrganizationStructure.objects.get(pk=1).rol.count()
        rol = Rol.objects.filter(pk=1).first()


        self.assertEqual(post_response.status_code, 302)
        self.assertContains(get_response, 'Solo Lectura')
        success_url = reverse('auth_and_perms:list_rol_by_org', args=[1])
        self.assertRedirects(post_response, success_url)
        self.assertTrue(pre_rol > pos_rol)
        self.assertIsNone(rol)

    def test_copy_rols(self):

        data = {
            'org_pk':1,
            'rols': [2]
        }
        pre_rol = OrganizationStructure.objects.get(pk=1).rol.count()

        post_response = self.client.post(reverse('auth_and_perms:copy_rols', kwargs={'pk':1}), data=data)
        pos_rol = OrganizationStructure.objects.get(pk=1).rol.count()


        self.assertEqual(post_response.status_code, 302)
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
            'first_name':'Vaca',
            'last_name':'Lola',
            'email':'lola@vaca.ac.cr',
            'phone_number':'6666-66-66',
            'id_card': '1331113',
            'job_position': 'Lechera',
            'ds_transaction': '135135313135',
            'organization': 1,
            'contentyperelobj':[37]
        }
        response = self.client.post(reverse('auth_and_perms:add_contenttype_to_org'),data=data)
        org_relations= OrganizationStructureRelations.objects.filter(organization__pk=1)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(org_relations.count() > 0)
        self.assertRedirects(response, reverse('auth_and_perms:organizationManager'))
