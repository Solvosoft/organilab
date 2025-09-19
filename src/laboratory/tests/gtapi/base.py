import json
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse
from auth_and_perms.organization_utils import organization_can_change_laboratory
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    Furniture,
    ShelfObject,
    LaboratoryRoom,
    Shelf,
)
from laboratory.shelfobject.utils import get_available_containers_for_selection
from laboratory.utils import check_user_access_kwargs_org_lab


class TestCaseBase(TestCase):
    fixtures = ["gtapi/gtapi_data.json"]

    def setUp(self):
        super().setUp()

        # ORG
        self.org1 = OrganizationStructure.objects.filter(name="Organization 1").first()
        self.org2 = OrganizationStructure.objects.filter(name="Organization 2").first()

        # USER
        self.user1 = get_user_model().objects.filter(username="user1").first()
        self.user2 = get_user_model().objects.filter(username="user2").first()
        self.user3 = get_user_model().objects.filter(username="user3").first()
        self.user4 = get_user_model().objects.filter(username="user4").first()

        # PROFILE
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        self.profile3 = self.user3.profile
        self.profile4 = self.user4.profile

        # ORGS BY USER
        self.user1_org1_list = (
            OrganizationStructure.os_manager.filter_organization_by_user(
                self.user1
            ).distinct()
        )
        self.user2_org2_list = (
            OrganizationStructure.os_manager.filter_organization_by_user(
                self.user2
            ).distinct()
        )

        # LABS
        self.lab1_org1 = Laboratory.objects.get(name="Lab 1")
        self.lab2_org2 = Laboratory.objects.get(name="Lab 2")
        self.lab3_org2 = Laboratory.objects.get(name="Lab 3")

        # INITIAL DATA

        self.lab_contenttype = ContentType.objects.filter(
            app_label="laboratory", model="laboratory"
        ).first()
        self.org_contenttype = ContentType.objects.filter(
            app_label="laboratory", model="organizationstructure"
        ).first()

        self.client1 = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.client4 = Client()
        self.client1.force_login(self.user1)
        self.client2.force_login(self.user2)
        self.client3.force_login(self.user3)
        self.client4.force_login(self.user4)

        # DEFAULT DATA
        self.lab = self.lab1_org1
        self.org = self.org1
        self.user = self.user1
        self.client = self.client1
        self.furniture = Furniture.objects.get(pk=1)
        self.labroom = LaboratoryRoom.objects.get(pk=1)
        self.shelfobject = ShelfObject.objects.get(pk=1)
        self.shelf = Shelf.objects.get(pk=1)

        self.data = {
            "shelfobject": self.shelfobject.pk,
            "page": 1,
            "laboratory": self.lab.pk,
            "organization": self.org.pk,
            "shelf": self.shelf.pk,
        }

    def check_tests(
        self, response, status_code, org_can_change, user_access, results_data=True
    ):
        """
        CHECK TESTS
        1) Check response status code equal to expected status code.
        2) Check if organization can or cannot change this laboratory.
        3) Check if user have or does not have permission to access in this organization and laboratory.
        4) Check if 'results' key exists in response serializer data.
        """

        results = []

        self.assertEqual(response.status_code, status_code)

        if "organization" in self.data and "laboratory" in self.data:
            if self.org and self.lab:
                has_permission = organization_can_change_laboratory(self.lab, self.org)
                self.assertEqual(has_permission, org_can_change)

            check_user_access = check_user_access_kwargs_org_lab(
                self.data["organization"], self.data["laboratory"], self.user
            )
            self.assertEqual(check_user_access, user_access)

        if response.content:
            response_data = json.loads(response.content)
            self.assertEqual("results" not in response_data, results_data)

            if not results_data:
                results = response_data["results"]

        return results

    def get_obj_by_shelfobject(
        self,
        user=None,
        client=None,
        org_can_manage=False,
        user_access=False,
        status_code=400,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        """
        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, status_code, org_can_manage, user_access)


class OrgDoesNotExists(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.org = None
        self.data.update({"organization": 9867})


class LabDoesNotExists(TestCaseBase):
    def setUp(self):
        super().setUp()
        self.lab = None
        self.data.update({"laboratory": 3678})


class WithoutOrg(TestCaseBase):

    def setUp(self):
        super().setUp()
        del self.data["organization"]


class WithoutLab(TestCaseBase):

    def setUp(self):
        super().setUp()
        del self.data["laboratory"]


class OrgCannotManageLab(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.lab = self.lab2_org2
        self.data.update({"laboratory": self.lab.pk})


class ShelfViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("shelf-list")
        self.data.update({"relfield": self.furniture.pk})
        del self.data["shelf"]


class ShelfViewTestOrgCanManageLab(ShelfViewTest):

    def get_obj_by_shelfobject(
        self,
        user=None,
        client=None,
        user_access=False,
        status_code=400,
        results_data=True,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        5) Check if first element in results object is in available shelves list.
        """

        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        results = self.check_tests(
            response, status_code, True, user_access, results_data
        )

        if results and "relfield" in self.data:
            available_shelves = list(
                Shelf.objects.filter(furniture=self.data["relfield"])
                .values_list("pk", flat=True)
                .exclude(pk=self.shelfobject.shelf.pk)
            )
            self.assertTrue(results[0]["id"] in available_shelves)


class FurnitureViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("furniture-list")
        self.data.update({"relfield": self.labroom.pk})
        del self.data["shelf"]


class FurnitureViewTestOrgCanManageLab(FurnitureViewTest):

    def get_obj_by_shelfobject(
        self,
        user=None,
        client=None,
        user_access=False,
        status_code=400,
        results_data=True,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        5) Check if first element in results object is in available furniture list.
        """

        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        results = self.check_tests(
            response, status_code, True, user_access, results_data
        )

        if results and "relfield" in self.data:
            available_furniture = list(
                Furniture.objects.filter(labroom=self.data["relfield"]).values_list(
                    "pk", flat=True
                )
            )
            self.assertTrue(results[0]["id"] in available_furniture)


class LabRoomViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("lab_room-list")
        del self.data["shelf"]


class LabRoomViewTestOrgCanManageLab(LabRoomViewTest):

    def get_obj_by_shelfobject(
        self,
        user=None,
        client=None,
        user_access=False,
        status_code=400,
        results_data=True,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        5) Check if first element in results object is in available laboratory room list.
        """

        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        results = self.check_tests(
            response, status_code, True, user_access, results_data
        )

        if results:
            available_labroom = list(
                LaboratoryRoom.objects.filter(laboratory=self.lab).values_list(
                    "pk", flat=True
                )
            )
            self.assertTrue(results[0]["id"] in available_labroom)


class ShelfObjectViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("available-container-search-list")
        del self.data["shelfobject"]

    def get_available_container_by_lab_and_shelf(
        self,
        user=None,
        client=None,
        org_can_manage=False,
        user_access=False,
        status_code=400,
        same_lab=False,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        """
        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        self.check_tests(response, status_code, org_can_manage, user_access)
        if "laboratory" in self.data and "shelf" in self.data:
            self.assertEqual(
                self.data["laboratory"] == self.shelf.furniture.labroom.laboratory.pk,
                same_lab,
            )


class ShelfObjectViewTestOrgCanManageLab(ShelfObjectViewTest):

    def get_available_container_by_lab_and_shelf(
        self,
        user=None,
        client=None,
        user_access=False,
        status_code=400,
        results_data=True,
        same_lab=False,
    ):
        """
        CHECK TESTS
        ...
        Previous detail checks are in check tests function
        ...
        5) Check if first element in results object is in available container list.
        """

        if user and client:
            self.user = user
            self.client = client
        response = self.client.get(self.url, data=self.data)
        results = self.check_tests(
            response, status_code, True, user_access, results_data
        )

        if "laboratory" in self.data and "shelf" in self.data:
            self.assertEqual(
                self.data["laboratory"] == self.shelf.furniture.labroom.laboratory.pk,
                same_lab,
            )

        if results:
            available_shelfobject = list(
                get_available_containers_for_selection(
                    self.lab.pk, self.shelf.pk
                ).values_list("pk", flat=True)
            )
            self.assertTrue(results[0]["id"] in available_shelfobject)


class ObjectOrgSearchViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("objectorgsearch-list")


class ObjectContainerCloningViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("container-for-cloning-search-list")


class ObjectOrgAvailableViewTest(TestCaseBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("objectorgavailable-list")
