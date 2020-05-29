from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.test import TestCase, RequestFactory
from demoQA.management import commands
from ..models import Laboratory
from ..views.furniture import FurnitureReportView

class FurnitureViewTestCase(TestCase):

    def setUp(self):
        call_command('loaddemo')
    
    def test_furniture_report_view_permissions(self):
        """tests that users with permissions can access this view"""
        lab = Laboratory.objects.filter(name="Laboratory 5").first()
        user = User.objects.filter(username="est_1").first()
        request = RequestFactory().get(reverse("laboratory:reports_furniture_detail", kwargs={"lab_pk": lab.id}))
        request.user = user 
        response = FurnitureReportView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        
