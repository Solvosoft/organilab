from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from laboratory.models import OrganizationStructure, Object


class TestCaseBase(TestCase):
    fixtures = ["select_organization/objects_by_organization.json"]

    def setUp(self):
        super().setUp()

        # ORG
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()

        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.user2 = get_user_model().objects.filter(username="user2").first()

        # PROFILE
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile

        self.client1 = Client()
        self.client2 = Client()

        self.client1.force_login(self.user1)
        self.client2.force_login(self.user2)

        # DEFAULT DATA
        self.org = self.org1
        self.user = self.user1
        self.client = self.client1
        self.object = Object.objects.get(pk=1)
        self.data = {
            "organization": self.org.pk
        }


    def check_user_in_organization(self, user=None, client=None, user_is_in_org=False, status_code=400):
        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, status_code)
        if self.org:
            user_in_org = self.org.users.filter(pk=self.user.pk).exists()
            self.assertEqual(user_in_org, user_is_in_org)


class ObjectsByOrganizationViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("objbyorg-list")

    def check_objects_result(self):
        pass

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        self.check_user_in_organization(user, client, user_in_org, status_code)
        self.check_objects_result()


class OrgDoesNotExists(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.org = None
        self.data.update({
            "organization": 9867
        })


class WithoutOrg(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.org = None
        del self.data["organization"]

class OrganizationsByUserViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("orgtree-list")

    def check_organizations_result(self):
        pass

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        #self.check_user_in_organization(user, client, user_in_org, status_code)
        self.check_organizations_result()


class ShelfObjectsByObjectViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.data.update({
            "object": self.object.pk
        })
        self.url = reverse("auth_and_perms:api-searchshelfobjectorg-list")

    def check_shelfobject_result(self):
        pass

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        self.check_user_in_organization(user, client, user_in_org, status_code)
        self.check_shelfobject_result()


class ObjectDoesNotExists(ShelfObjectsByObjectViewTest):

    def setUp(self):
        super().setUp()
        self.object = None
        self.data.update({
            "object": 9867
        })

class WithoutObject(ShelfObjectsByObjectViewTest):

    def setUp(self):
        super().setUp()
        self.object = None
        del self.data["object"]


