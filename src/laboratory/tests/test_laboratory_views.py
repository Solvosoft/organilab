from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlencode
from django.test import TestCase
from .utils import TestUtil
from ..models import Laboratory, OrganizationStructure

class LaboratoryViewTestCase(TestCase):

    def setUp(self):
        util = TestUtil()
        util.populate_db()
        self.admin_dep3 = User.objects.filter(username="udep_3").first()
        self.admin_schi1 = User.objects.filter(username="uschi1").first()
        self.admin =  User.objects.filter(username="udep1_2").first()
        self.student = User.objects.filter(username="est_1").first()
        self.lab8 = Laboratory.objects.filter(name="Laboratory 8").first()
        self.lab5 = Laboratory.objects.filter(name="Laboratory 5").first()
        self.lab3 = Laboratory.objects.filter(name="Laboratory 3").first()
        self.lab4 = Laboratory.objects.filter(name="Laboratory 4").first()
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
        self.assertTemplateUsed(response, 'laboratory/laboratory_notperm.html')
    
    def test_laboratory_create_view_post_student(self):
        """tests that submitting a form with student user won't create a lab"""
        url = reverse("laboratory:create_lab")
        data = urlencode({            
            "name": "test_laboratory",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin).first().id
            })
        self.client.force_login(self.student) 
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertTemplateUsed(response, 'laboratory/laboratory_notperm.html')
    
    def test_laboratory_update_view_get_student(self):
        """tests that users without permissions can't get to the update view"""
        kwargs = { "pk": self.lab5.id }
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'laboratory/edit.html')
        self.assertTemplateUsed(response, 'laboratory/action_denied.html')
    
    def test_laboratory_update_view_post_student(self):
        """tests that users without permissions can't post to the update view"""
        kwargs = {"pk": self.lab5.id }
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        self.client.force_login(self.student)
        data = urlencode({            
            "name": "updated name",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin).first().id
            })
        response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
        self.assertTemplateUsed(response, 'laboratory/action_denied.html', 
                                          "Was expecting to be redirected to action denied page")

    def test_laboratory_delete_view_student(self):
        """tests that users without permissions can't delete labs"""
        saved_id = self.lab5.id
        kwargs = { "pk": self.lab5.id }
        url = reverse("laboratory:laboratory_delete", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.post(url, follow=True)
        self.assertIsNotNone(Laboratory.objects.filter(id=saved_id).first(),
                             "Was not expecting to delete a lab!")
    
    def test_laboratory_hcodereport_view_student(self):
        """tests that the student is unable to access the hcode report view"""
        url = reverse("laboratory:h_code_reports")
        self.client.force_login(self.student) 
        response = self.client.get(url)
        self.assertTemplateNotUsed(response, 'laboratory/h_code_report.html',
                                             "was not expecting to access this view with student user")
    
    #TODO admin can do HCODEREPORT

    def test_laboratory_create_view_get_admin(self):
        """tests that admin user can get to the create laboratory view"""
        url = reverse("laboratory:create_lab")
        self.client.force_login(self.admin)  
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "laboratory/laboratory_create.html")
    
    def test_laboratory_create_view_post_admin(self):
        """tests that admin user can post and create a new laboratory"""
        url = reverse("laboratory:create_lab")
        self.client.force_login(self.admin)
        data = urlencode({
            "name": "test_laboratory",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin).first().id
            })
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 200)
        #should be redirected to the room creation form
        self.assertTemplateUsed(response, "laboratory/laboratoryroom_form.html",
                                          "was expencting to be redirected to the room creation form")  

    def test_laboratory_update_view_post_admin(self):
        """tests that admin user can post and update a laboratory"""
        kwargs = {"pk": self.lab5.id}
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        data = urlencode({
            "name": "updated_name",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin).first().id
        })
        self.client.force_login(self.admin)  
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 200)
        #should redirect to the laboratory list view
        self.assertTemplateUsed(response, 'laboratory/laboratory_list.html',
                                          "Was expecting to be redirected to the laboratory list view")
    
    def test_laboratory_delete_view_admin(self):
        """tests that admin users can delete a lab"""
        saved_id = self.lab5.id
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_delete", kwargs=kwargs)
        self.client.force_login(self.admin)
        response = self.client.post(url, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertRaises(Laboratory.DoesNotExist, Laboratory.objects.get, id=saved_id)
    
    def test_laboratory_outside_admin_create_view(self):
        """tests that admin from dep1_2 can't create a lab in dep3"""
        url = reverse("laboratory:create_lab")
        self.client.force_login(self.admin)
        data = urlencode({
            "name": "test_laboratory",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin_dep3).first().id
            })
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 200)
        #should be redirected to the lab creation form (with errors)
        self.assertTemplateUsed(response, "laboratory/laboratory_create.html", 
                                          "Was expecting to be redirected to the creation form")  

    def test_laboratory_outside_admin_update_view(self):
        """tests that admin from dep3 can't update a lab in dep2"""
        kwargs = {"pk": self.lab5.id }
        url = reverse("laboratory:laboratory_update", kwargs=kwargs)
        self.client.force_login(self.admin_dep3)
        data = urlencode({            
            "name": "updated name",
            "phone_number": 5555555,
            "location":"San Jose",
            "geolocation": "12345645, 1234455588",
            "organization": OrganizationStructure.os_manager.filter_user(self.admin).first().id
            })
        response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
        self.assertTemplateUsed(response, 'laboratory/edit.html', 
                                          "Was expecting to be redirected to laboratory edit view")
    
    def test_laboratory_outside_admin_delete_view(self):
        """tests that admins from other orgs can't delete labs"""
        saved_id = self.lab5.id
        kwargs = { "pk": self.lab5.id }
        url = reverse("laboratory:laboratory_delete", kwargs=kwargs)
        self.client.force_login(self.admin_dep3)
        response = self.client.post(url, follow=True)
        self.assertIsNotNone(Laboratory.objects.filter(id=saved_id).first(),
                             "Was not expecting to delete a lab!")

    def test_laboratory_select_view_student(self):
        """tests that students can access select lab view"""
        url = reverse("laboratory:select_lab")
        self.client.force_login(self.student) 
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "laboratory/select_lab.html")
    
    def test_laboratory_select_view_admin(self):
        """tests that admins can access select lab view"""
        url = reverse("laboratory:select_lab")
        self.client.force_login(self.student) 
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "laboratory/select_lab.html")
    
    """ajax views"""

    def test_laboratory_ajax_admins_users_list_student(self):
        """test that a student is not able to access this view"""
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_list.html", 
                                             "Was not expecting to get to this page as a student")
    
    def test_laboratory_ajax_admins_users_list_anonymous(self):
        """test that anonymous user is not able to access this view"""
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_list.html", 
                                             "Was not expecting to get to this page without a logged in user")
    
    def test_laboratory_ajax_admins_users_list_admin(self):
        """test that admin from dep2 is able to access this view"""
        kwargs = { "pk": self.lab4.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        self.client.force_login(self.admin)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, "ajax/lab_admins_list.html", 
                                             "Was expecting to get to this page as a lab admin")
        
    def test_laboratory_ajax_admins_users_list_outside_admin(self):
        """test that admin from isch1 is not able to access admins in lab 4"""
        kwargs = { "pk": self.lab4.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        self.client.force_login(self.admin_schi1)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_list.html", 
                                             "Was not expecting to get to this page with admin schi1")
    
    def test_laboratory_ajax_get_create_admins_user_anonymous(self):
        """test that anonymous users are not able to get to this view"""
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_ajax_get_create_admins_user", kwargs=kwargs)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_create.html", 
                                             "Was not expecting to get to this page without a logged in user")
    
    def test_laboratory_ajax_get_create_admins_user_student(self):
        """test that student users are not able to get to this view"""
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_ajax_get_create_admins_user", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_create.html", 
                                             "Was not expecting to get to this page with a student user")
    
    def test_laboratory_ajax_get_create_admins_user_admin(self):
        """test that admin from dep3 is able to access this view in lab 8"""
        kwargs = { "pk": self.lab8.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        self.client.force_login(self.admin_dep3)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, "ajax/lab_admins_list.html", 
                                             "Was expecting to get to this page as a lab admin")

    def test_laboratory_ajax_get_create_admins_user_dep3_admin(self):
        """test that admin from dep3 is not able to access this view in lab 5"""
        kwargs = { "pk": self.lab5.id}
        url = reverse("laboratory:laboratory_ajax_admins_users_list", kwargs=kwargs)
        self.client.force_login(self.admin_dep3)
        response = self.client.get(url, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_list.html", 
                                             "Was not expecting to get to this page in lab5 as a dep3 admin")

    def test_laboratory_ajax_create_admins_user_anonymous(self):
        """test that anonymous users are not able to post to this view and create a lab admin"""
        #laboratory_ajax_create_admins_user is broken, we need to fix it, 
        #'Laboratory' object has no attribute 'lab_admins'
        kwargs = { "pk": self.lab5.id}
        data = urlencode({            
            'username': "test_admin",
            'email': "patito@gmail.com",
            'password': "supersecretpassword"
            })
        url = reverse("laboratory:laboratory_ajax_create_admins_user", kwargs=kwargs)
        response = self.client.post(url, data, content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateNotUsed(response, "ajax/lab_admins_create.html", 
                                             "Was not expecting to create an admin without a logged in user")
    