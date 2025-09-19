from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from auth_and_perms.node_tree import (
    get_org_parents_info,
    get_tree_organization_pks_by_user,
)
from laboratory.models import OrganizationStructure, Object, ShelfObject
import json


class TestCaseBase(TestCase):
    fixtures = ["select_organization/objects_by_organization.json"]

    def setUp(self):
        super().setUp()
        # ORG
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()

        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.user2 = get_user_model().objects.filter(username="user2").first()
        self.user3 = get_user_model().objects.filter(username="user3").first()
        self.user4 = get_user_model().objects.filter(username="user4").first()
        self.user5 = get_user_model().objects.filter(username="user5").first()

        # PROFILE
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        self.profile3 = self.user3.profile
        self.profile4 = self.user4.profile
        self.profile5 = self.user5.profile

        self.client1 = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.client4 = Client()
        self.client5 = Client()

        self.client1.force_login(self.user1)
        self.client2.force_login(self.user2)
        self.client3.force_login(self.user3)
        self.client4.force_login(self.user4)
        self.client5.force_login(self.user5)

        # DEFAULT DATA
        self.org = self.org1
        self.user = self.user1
        self.client = self.client1
        self.object = Object.objects.get(pk=1)
        self.data = {"organization": self.org.pk}

    def check_user_in_organization(self, user=None, client=None, user_is_in_org=False):
        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)

        if self.org:
            user_in_org = self.org.users.filter(pk=self.user.pk).exists()
            self.assertEqual(user_in_org, user_is_in_org)
        return response

    def check_status_code(self, response, status_code=400):
        self.assertEqual(response.status_code, status_code)

        content = json.loads(response.content)

        if status_code == 400:
            self.assertTrue(content["errors"])

        if status_code == 403:
            self.assertTrue(content["detail"])


class ObjectsByOrganizationViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("objbyorg-list")

    def check_objects_result(self, response, status_code):
        objects_org = Object.objects.filter(organization=self.org)
        object_id_list = list(objects_org.values_list("id", flat=True).order_by("name"))
        content = json.loads(response.content)

        if status_code == 200:
            if objects_org.exists():
                obj_response_list = [obj["id"] for obj in content["results"]]
                self.assertTrue(content["results"])
                self.assertEqual(objects_org.count(), content["total_count"])
                self.assertEqual(object_id_list, obj_response_list)
            else:
                self.assertFalse(content["results"])
                self.assertEqual(content["total_count"], 0)

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        response = self.check_user_in_organization(user, client, user_in_org)
        self.check_status_code(response, status_code)
        self.check_objects_result(response, status_code)


class OrgDoesNotExists(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.org = None
        self.data.update({"organization": 9867})


class WithoutOrg(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.org = None
        del self.data["organization"]


class OrganizationsByUserViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("orgtree-list")
        self.org = None

    def check_level(self, org):
        self.assertEqual(org.parent.level + 1, org.level)

    def check_position(self, org):
        self.assertTrue(org.parent.position < org.position)

    def check_org_detail(self, org_pk_tree):
        for i, org_pk in enumerate(org_pk_tree):
            org = OrganizationStructure.objects.get(pk=org_pk)

            if org.parent:
                if org.parent.pk in org_pk_tree:
                    self.assertTrue(i > org_pk_tree.index(org.parent.pk))

                # check not related parent to user if not in org tree result
                if i == 0 and self.user == self.user5:
                    self.assertTrue(org.parent.pk not in org_pk_tree)

            if org.level:
                self.check_level(org)

                if org.position:
                    self.check_position(org)
            else:
                self.assertTrue(org.parent is None)

    def get_organizations_id_by_user(self):
        parents, parents_pks = get_org_parents_info(self.user)
        pks = []
        for node in parents:
            if node.pk not in pks:
                get_tree_organization_pks_by_user(
                    node, self.user, pks, parents=parents_pks, extras={"active": True}
                )

        return pks

    def check_organizations_result(self, response, status_code):
        organization_id_list = self.get_organizations_id_by_user()
        org_exclude_list = OrganizationStructure.objects.exclude(
            pk__in=organization_id_list
        )
        content = json.loads(response.content)

        if status_code == 200:
            if len(organization_id_list):
                organization_response_list = [obj["id"] for obj in content["results"]]
                self.assertTrue(content["results"])
                self.assertEqual(len(organization_id_list), content["total_count"])
                self.assertEqual(organization_id_list, organization_response_list)

                for org in org_exclude_list:
                    self.assertTrue(org.pk not in organization_response_list)

                self.check_org_detail(organization_id_list)
            else:
                self.assertFalse(content["results"])
                self.assertEqual(content["total_count"], 0)

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        response = self.check_user_in_organization(user, client, user_in_org)
        self.check_status_code(response, status_code)
        self.check_organizations_result(response, status_code)


class ShelfObjectsByObjectViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.data.update({"object": self.object.pk})
        self.url = reverse("auth_and_perms:api-searchshelfobjectorg-list")

    def check_shelfobject_result(self, response, status_code):
        shelfobjects_by_object_and_org = ShelfObject.objects.filter(
            in_where_laboratory__organization=self.org, object=self.object
        ).distinct()
        shelfobjects_id_list = list(
            shelfobjects_by_object_and_org.values_list("id", flat=True).order_by("id")
        )
        content = json.loads(response.content)

        if status_code == 200:
            if shelfobjects_by_object_and_org.exists():
                shelfobject_response_list = [obj["id"] for obj in content["data"]]
                self.assertTrue(content["data"])
                self.assertEqual(
                    shelfobjects_by_object_and_org.count(), content["recordsTotal"]
                )
                self.assertEqual(shelfobjects_id_list, shelfobject_response_list)
            else:
                self.assertFalse(content["data"])
                self.assertEqual(content["recordsTotal"], 0)

    def check_tests(self, user=None, client=None, user_in_org=False, status_code=400):
        response = self.check_user_in_organization(user, client, user_in_org)
        self.check_status_code(response, status_code)
        self.check_shelfobject_result(response, status_code)


class ObjectDoesNotExists(ShelfObjectsByObjectViewTest):

    def setUp(self):
        super().setUp()
        self.object = None
        self.data.update({"object": 9867})


class WithoutObject(ShelfObjectsByObjectViewTest):

    def setUp(self):
        super().setUp()
        self.object = None
        del self.data["object"]


class OrganizationButtonsByUserViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("auth_and_perms:api_organization_buttons")

    def check_organization_buttons_result(
        self, response, status_code, can_view_actions_buttons
    ):
        content = json.loads(response.content)

        if status_code == 200:
            self.assertTrue(self.org.name in content["result"])
            self.assertEqual(
                "btn-success" in content["result"], can_view_actions_buttons
            )
            self.assertEqual(
                "btn-primary" in content["result"], can_view_actions_buttons
            )
            self.assertEqual(
                "btn-secondary" in content["result"], can_view_actions_buttons
            )
            self.assertEqual("btn-dark" in content["result"], can_view_actions_buttons)
            self.assertEqual(
                "btn-danger" in content["result"], can_view_actions_buttons
            )

    def check_tests(
        self,
        user=None,
        client=None,
        user_in_org=False,
        status_code=400,
        can_view_actions_buttons=False,
    ):
        response = self.check_user_in_organization(user, client, user_in_org)
        self.check_status_code(response, status_code)
        self.check_organization_buttons_result(
            response, status_code, can_view_actions_buttons
        )
