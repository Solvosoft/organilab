from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.utils.http import urlencode
from django.test import TestCase, RequestFactory
from demoQA.management import commands
from .utils import TestUtil
from ..models import ( 
    Laboratory, 
    LaboratoryRoom,
    Furniture,
    Catalog
)
from ..views.furniture import ( 
    FurnitureReportView, 
    FurnitureCreateView,
    FurnitureUpdateView
)

class FurnitureViewTestCase(TestCase):

    def setUp(self):
        util = TestUtil()
        util.populate_db()
        self.admin =  User.objects.filter(username="udep1_2").first()
        self.student = User.objects.filter(username="est_1").first()
        self.lab = Laboratory.objects.filter(name="Laboratory 5").first()
        self.room = LaboratoryRoom.objects.create(name="test_room")
        self.lab.rooms.add(self.room)
        catalog = Catalog.objects.filter(key="furniture_type").first()
        self.furniture = Furniture.objects.create(labroom=self.room, name="test_furniture", type=catalog)
    
    def test_furniture_report_view_permissions(self):
        """tests that users without permissions can't access furniture report view"""
        kwargs = {"lab_pk": self.lab.id }
        url = reverse("laboratory:reports_furniture_detail", kwargs=kwargs)
        self.client.force_login(self.student) 
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_furniture_create_view_get_permissions(self):
        """tests that users without permissions can't get to this view"""
        kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
        url = reverse("laboratory:furniture_create", kwargs=kwargs)
        self.client.force_login(self.student)  
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    def test_furniture_create_view_post_permissions(self):
        """tests that submitting a form without permissions won't create a furniture"""
        kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
        url = reverse("laboratory:furniture_create", kwargs=kwargs)
        data = urlencode({"name": "test_furniture", "type": "F"})
        self.client.force_login(self.student) 
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    def test_furniture_update_view_get_permissions(self):
        """tests that users without permissions can't get to the update view"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    def test_furniture_update_view_post_permissions(self):
        """tests that users without permissions can't post to the update view"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        self.client.force_login(self.student)
        data = urlencode({"name": "modified"})
        response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

    def test_furniture_delete_view_permissions(self):
        """tests that users without permissions can't delete furnitures"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_delete", kwargs=kwargs)
        self.client.force_login(self.student)
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    def test_furniture_report_view_admin(self):
        """tests that the user udep1_2 is able to access the furniture report view"""
        kwargs = {"lab_pk": self.lab.id }
        url = reverse("laboratory:reports_furniture_detail", kwargs=kwargs)
        self.client.force_login(self.admin) 
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_furniture_create_view_get_admin(self):
        """tests that admin user can get to the create furniture view"""
        kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
        url = reverse("laboratory:furniture_create", kwargs=kwargs)
        self.client.force_login(self.admin)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_furniture_update_view_get_admin(self):
        """tests that admin user can get to the create furniture view"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        self.client.force_login(self.admin)  
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_furniture_create_view_post_admin(self):
        """tests that admin user can post and create a new furniture"""
        kwargs = { "lab_pk": self.lab.id, "labroom": self.room.id }
        url = reverse("laboratory:furniture_create", kwargs=kwargs)
        data = urlencode({"name": "test_furniture", "type": "F"})
        self.client.force_login(self.admin)
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_furniture_update_view_post_admin(self):
        """tests that admin user can post and update a furniture"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        data = urlencode({"name": "updated name"})
        self.client.force_login(self.admin)  
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_furniture_delete_view_admin(self):
        """tests that admin users can delete furnitures"""
        kwargs = { "lab_pk": self.lab.id, "pk": self.furniture.id }
        url = reverse("laboratory:furniture_delete", kwargs=kwargs)
        self.client.force_login(self.admin)
        response = self.client.get(url, follow=True)
        self.assertEquals(response.status_code, 200)