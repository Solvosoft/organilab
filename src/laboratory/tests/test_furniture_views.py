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
    
    def test_furniture_report_view_permissions(self):
        """tests that users without permissions can't access furniture report view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        kwargs = {"lab_pk": lab.id }
        request = RequestFactory().get(reverse("laboratory:reports_furniture_detail", kwargs=kwargs))
        request.user = user 
        response = FurnitureReportView.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 403)

    def test_furniture_create_view_get_permissions(self):
        """tests that users without permissions can't get to this view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        room = LaboratoryRoom.objects.create(name="test_room")
        lab.rooms.add(room)
        kwargs = { "lab_pk": lab.id, "labroom": room.id }
        request = RequestFactory().get(reverse("laboratory:furniture_create", kwargs=kwargs))
        request.user = user 
        response = FurnitureCreateView.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 403)
    
    def test_furniture_create_view_post_permissions(self):
        """tests that submitting a form without permissions won't create a furniture"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        room = LaboratoryRoom.objects.create(name="test_room")
        lab.rooms.add(room)
        kwargs = { "lab_pk": lab.id, "labroom": room.id }
        url = reverse("laboratory:furniture_create", kwargs=kwargs)
        data = urlencode({"name": "test_furniture", "type": "F"})
        self.client.force_login(user) 
        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded", follow=True)
        self.assertEqual(response.status_code, 403)
    
    def test_furniture_update_view_get_permissions(self):
        """tests that users without permissions can't get to the update view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        room = LaboratoryRoom.objects.create(name="test_room")
        lab.rooms.add(room)
        catalog = Catalog.objects.filter(key="furniture_type").first()
        furniture = Furniture.objects.create(labroom=room, name="test_furniture", type=catalog)
        kwargs = { "lab_pk": lab.id, "pk": furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        self.client.force_login(user)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)
    
    def test_furniture_update_view_post_permissions(self):
        """tests that users without permissions can't post to the update view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        room = LaboratoryRoom.objects.create(name="test_room")
        lab.rooms.add(room)
        catalog = Catalog.objects.filter(key="furniture_type").first()
        furniture = Furniture.objects.create(labroom=room, name="test_furniture", type=catalog)
        kwargs = { "lab_pk": lab.id, "pk": furniture.id }
        url = reverse("laboratory:furniture_update", kwargs=kwargs)
        self.client.force_login(user)
        data = urlencode({"name": "modified"})
        response = self.client.post(url, data,  content_type="application/x-www-form-urlencoded", follow=True)
        self.assertRedirects(response, reverse('permission_denied'), 302, 200)

