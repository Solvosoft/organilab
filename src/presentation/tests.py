from django.test import TestCase
from djgentelella.models import PermissionsCategoryManagement



class MyTest(TestCase):
    fixtures = ["initialdata"]

    def test_should_create_group(self):
        pcm = PermissionsCategoryManagement.objects.get(pk=199)
        self.assertEqual(pcm.url_name, "index")