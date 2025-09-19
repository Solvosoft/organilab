from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import Laboratory
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission


class ShelfObjectAPITest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)
        self.user3 = User.objects.get(pk=3)
        self.org_pk = 1
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)
        user2_role = Rol.objects.create(name="Test Role for User 2", color="#FFF")
        permission = Permission.objects.filter(codename__contains="shelfobject")
        user2_role.permissions.add(*permission)
        profile_permission = ProfilePermission.objects.create(
            profile=self.user2.profile,
            object_id=2,
            content_type=ContentType.objects.get(
                app_label="laboratory", model="organizationstructure"
            ),
        )
        profile_permission.rol.add(user2_role)
