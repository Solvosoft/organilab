from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.test import TestCase, RequestFactory
from demoQA.management import commands
from .utils import TestUtil
from ..models import Laboratory, LaboratoryRoom
from ..views.furniture import FurnitureReportView, FurnitureCreateView

class FurnitureViewTestCase(TestCase):

    def setUp(self):
        util = TestUtil()
        util.populate_db()
    
    def test_furniture_report_view_permissions(self):
        """tests that users without permissions can't access furniture report view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        kwargs = {"lab_pk": lab.id}
        request = RequestFactory().get(reverse("laboratory:reports_furniture_detail", kwargs=kwargs))
        request.user = user 
        response = FurnitureReportView.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 403)

    def test_furniture_add_view_permissions(self):
        """tests that users withou permissions can't create a furniture"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        room = LaboratoryRoom.objects.create(name="test_room")
        lab.rooms.add(room)
        kwargs = {"lab_pk": lab.id, "labroom": room.id }
        request = RequestFactory().get(reverse("laboratory:furniture_create", kwargs=kwargs))
        request.user = user 
        response = FurnitureCreateView.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 403)   

    
