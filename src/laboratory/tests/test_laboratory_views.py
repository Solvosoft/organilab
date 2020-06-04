from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlencode
from django.test import TestCase
from .utils import TestUtil
from ..models import Laboratory

class LaboratoryViewTestCase(TestCase):

    def setUp(self):
        util = TestUtil()
        util.populate_db()
        self.admin_dep3 = User.objects.filter(username="udep_3").first()
        self.admin_schi1 = User.objects.filter(username="uschi1").first()
        self.admin =  User.objects.filter(username="udep1_2").first()
        self.student = User.objects.filter(username="est_1").first()
        self.lab5 = Laboratory.objects.filter(name="Laboratory 5").first()
        self.lab3 = Laboratory.objects.filter(name="Laboratory 3").first()
        self.lab6 = Laboratory.objects.filter(name="Laboratory 6").first()
        self.lab7 = Laboratory.objects.filter(name="Laboratory 7").first()
    
    def test_laboratory_list_view_student(self):
        """tests that students can access lab list view"""
        url = reverse("laboratory:mylabs")
        self.client.force_login(self.student) 
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_laboratory_list_view_anonymous(self):
        """tests that students can't access list view"""
        url = reverse("laboratory:mylabs")
        response = self.client.get(url, follow=True)
        self.assertContains(response, reverse('login'))

    def test_laboratory_create_view_get_student(self):
        """tests that students can't get to this view"""
        url = reverse("laboratory:create_lab")
        self.client.force_login(self.student)  
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed('laboratory/laboratory_notperm.html')
    
    def test_laboratory_create_view_post_student(self):
        """tests that submitting a form with student user won't create a lab"""
        url = reverse("laboratory:create_lab")
        data = urlencode({"name": "test_laboratory", "phone_number": 5555555})
        self.client.force_login(self.student) 
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertTemplateUsed('laboratory/laboratory_notperm.html')
    
    def test_laboratory_update_view_get_student(self):
        """tests that users without permissions can't get to the update view"""
        kwargs = { "pk": self.lab5.id }
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed('laboratory/edit.html')
        self.assertTemplateUsed('laboratory/action_denied.html')
    
    def test_laboratory_update_view_post_student(self):
        """tests that users without permissions can't post to the update view"""
        kwargs = {"pk": self.lab5.id }
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        self.client.force_login(self.student)
        data = urlencode({"name": "modified"})
        response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
        self.assertTemplateUsed('laboratory/action_denied.html')

    def test_laboratory_delete_view_student(self):
        """tests that users without permissions can't delete labs"""
        kwargs = { "pk": self.lab5.id }
        url = reverse("laboratory:laboratory_delete", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.post(url, follow=True)
        self.assertTemplateUsed('laboratory/action_denied.html')
    
    # def test_laboratory_report_view_admin(self):
    #     """tests that the user udep1_2 is able to access the furniture report view"""
    #     kwargs = {"lab_pk": self.lab.id }
    #     url = reverse("laboratory:reports_laboratory_detail", kwargs=kwargs)
    #     self.client.force_login(self.admin) 
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    
    # def test_laboratory_create_view_get_admin(self):
    #     """tests that admin user can get to the create furniture view"""
    #     kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
    #     url = reverse("laboratory:furniture_create", kwargs=kwargs)
    #     self.client.force_login(self.admin)
    #     response = self.client.get(url, follow=True)
    #     self.assertEqual(response.status_code, 200)
    
    # def test_laboratory_update_view_get_admin(self):
    #     """tests that admin user can get to the update furniture view"""
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
    #     url = reverse("laboratory:furniture_update", kwargs=kwargs)
    #     self.client.force_login(self.admin)  
    #     response = self.client.get(url, follow=True)
    #     self.assertEqual(response.status_code, 200)
    
    # def test_laboratory_create_view_post_admin(self):
    #     """tests that admin user can post and create a new furniture"""
    #     kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
    #     url = reverse("laboratory:furniture_create", kwargs=kwargs)
    #     data = urlencode({"name": "test_furniture", "type": "F"})
    #     self.client.force_login(self.admin)
    #     response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
    #     self.assertEqual(response.status_code, 200)

    # def test_laboratory_update_view_post_admin(self):
    #     """tests that admin user can post and update a furniture"""
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
    #     url = reverse("laboratory:furniture_update", kwargs=kwargs)
    #     data = urlencode({"name": "updated name"})
    #     self.client.force_login(self.admin)  
    #     response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
    #     self.assertEqual(response.status_code, 200)
    
    # def test_laboratory_delete_view_admin(self):
    #     """tests that admin users can delete furnitures"""
    #     saved_id = self.furniture.id
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id}
    #     url = reverse("laboratory:furniture_delete", kwargs=kwargs)
    #     self.client.force_login(self.admin)
    #     response = self.client.post(url, follow=True)
    #     self.assertEquals(response.status_code, 200)
    #     self.assertRaises(Furniture.DoesNotExist, Furniture.objects.get, id=saved_id)
    
    # def test_laboratory_list_view_student(self):
    #     """tests that student users can't see furniture lists"""
    #     kwargs = { "lab_pk": self.lab.id}
    #     url = reverse("laboratory:furniture_list", kwargs=kwargs)
    #     self.client.force_login(self.student)
    #     response = self.client.get(url, content_type='application/json',HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    # def test_laboratory_list_view_admin(self):
    #     """tests that admim users are able to see furniture lists"""
    #     kwargs = { "lab_pk": self.lab.id}
    #     url = reverse("laboratory:furniture_list", kwargs=kwargs)
    #     self.client.force_login(self.admin)
    #     response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #     self.assertEqual(response.status_code, 200)
    
    # def test_laboratory_outside_admin_report_view(self):
    #     """tests that an admin from isch1 can not get to the report in lab 5"""
    #     kwargs = {"lab_pk": self.lab.id }
    #     url = reverse("laboratory:reports_laboratory_detail", kwargs=kwargs)
    #     self.client.force_login(self.admin_schi1) 
    #     response = self.client.get(url, follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    # def test_laboratory_outside_admin_create_view_get(self):
    #     """tests that admin from isch1 can't get to this view in lab 5"""
    #     kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
    #     url = reverse("laboratory:furniture_create", kwargs=kwargs)
    #     self.client.force_login(self.admin_schi1)  
    #     response = self.client.get(url, follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    # def test_laboratory_outside_admin_create_view_post(self):
    #     """tests that admin from dep3 can't post to this view in lab 5"""
    #     kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
    #     url = reverse("laboratory:furniture_create", kwargs=kwargs)
    #     data = urlencode({"name": "test_furniture", "type": "F"})
    #     self.client.force_login(self.admin_dep3) 
    #     response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    # def test_laboratory_outside_admin_update_view_get(self):
    #     """tests that admin from dep3 can't get to the update view in lab 5"""
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
    #     url = reverse("laboratory:furniture_update", kwargs=kwargs)
    #     self.client.force_login(self.admin_dep3)
    #     response = self.client.get(url, follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    # def test_laboratory_outside_admin_update_view_post(self):
    #     """tests that admin from isch1 can't post to the update view in lab 5"""
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
    #     url = reverse("laboratory:furniture_update", kwargs=kwargs)
    #     self.client.force_login(self.admin_schi1)
    #     data = urlencode({"name": "modified"})
    #     response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    # def test_laboratory_outside_admin_delete_view(self):
    #     """tests that admins from other orgs can't delete furnitures"""
    #     kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
    #     url = reverse("laboratory:furniture_delete", kwargs=kwargs)
    #     self.client.force_login(self.admin_schi1)
    #     response = self.client.post(url, follow=True)
    #     self.assertRedirects(response, reverse('permission_denied'), 302, 200)
