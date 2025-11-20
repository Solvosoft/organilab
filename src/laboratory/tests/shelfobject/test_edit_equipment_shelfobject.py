from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import (
    Laboratory,
    ShelfObjectObservation,
    ShelfObject,
    Catalog,
    UserOrganization,
    OrganizationStructure,
    Shelf,
    Object,
    ShelfObjectEquipmentCharacteristics,
)
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils.translation import gettext_lazy as _
import json


class EditShelfobject(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.user1 = User.objects.get(pk=3)
        self.org_pk = 1
        self.lab = Laboratory.objects.first()
        create_status_rol = Rol.objects.create(
            name="Test edit shelfobject", color="#FFF"
        )
        permission = Permission.objects.filter(codename="change_shelfobject")
        create_status_rol.permissions.add(*permission)
        profile_permission = ProfilePermission.objects.create(
            profile=self.user.profile,
            object_id=1,
            content_type=ContentType.objects.get(
                app_label="laboratory", model="organizationstructure"
            ),
        )
        profile_permission.rol.add(create_status_rol)
        org = OrganizationStructure.objects.get(pk=1)
        user_org = UserOrganization.objects.create(
            organization=org, user=self.user, type_in_organization=1
        )
        org.users.add(self.user)
        self.client.force_login(self.user)
        self.data = {
            "shelfobject": 13,
            "status": 1,
            "description": 1,
            "provider": "",
            "authorized_roles_to_use_equipment": [create_status_rol.pk],
            "equipment_price": 200,
            "have_guarantee": True,
            "contract_of_maintenance": "",
            "available_to_use": False,
            "notes": "New characteristic",
        }

    def test_edit_shelfobject_equipment_without_characterics(self):

        pre_shelfobject = ShelfObject.objects.get(pk=13)
        pre_shelfobject = hasattr(
            pre_shelfobject, "shelfobjectequipmentcharacteristics"
        )

        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 13},
        )
        response = self.client.put(url, data=self.data, content_type="application/json")
        pos_shelfobject = ShelfObject.objects.get(pk=13)
        self.assertTrue(hasattr(pos_shelfobject, "shelfobjectequipmentcharacteristics"))
        self.assertFalse(pre_shelfobject)
        self.assertTrue(
            json.loads(response.content)["detail"]
            == _("Shelfobject was updated successfully.")
        )
        self.assertEqual(response.status_code, 200)

    def test_create_shelfobject_other_lab(self):

        self.client.logout()
        self.client.force_login(self.user)
        org = OrganizationStructure.objects.get(pk=2)
        lab = Laboratory.objects.create(name="Lab x", organization=org)

        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": lab.pk, "pk": 13},
        )

        response = self.client.put(url, data=self.data, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            json.loads(response.content)["detail"]
            == _("You can modify this laboratory")
        )

    def test_edit_shelfobject_other_organization(self):

        self.client.logout()
        self.client.force_login(self.user)

        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": 4, "lab_pk": self.lab.pk, "pk": 13},
        )

        response = self.client.put(url, data=self.data, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            json.loads(response.content)["detail"]
            == _("You do not have permission to perform this action.")
        )

    def test_edit_shelfobject_equipment(self):

        new_data = self.data.copy()
        new_data["shelfobject"] = 15
        pre_shelfobject = ShelfObject.objects.get(pk=15)
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        pos_shelfobject = ShelfObject.objects.get(pk=15)
        self.assertTrue(hasattr(pos_shelfobject, "shelfobjectequipmentcharacteristics"))
        self.assertTrue(hasattr(pre_shelfobject, "shelfobjectequipmentcharacteristics"))
        self.assertTrue(
            json.loads(response.content)["detail"]
            == _("Shelfobject was updated successfully.")
        )
        self.assertEqual(response.status_code, 200)

    def test_edit_shelfobject_negative_price(self):

        new_data = self.data.copy()
        new_data["shelfobject"] = 15
        new_data["equipment_price"] = -1
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")

        self.assertTrue(
            json.loads(response.content)["equipment_price"][0]
            == _("Ensure this value is greater than or equal to 0.")
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_shelfobject_price_str(self):

        new_data = self.data.copy()
        new_data["shelfobject"] = 15
        new_data["equipment_price"] = "fafafsa"
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        self.assertTrue(
            json.loads(response.content)["equipment_price"][0]
            == _("A valid number is required.")
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_shelfobject_price_empty(self):

        new_data = self.data.copy()
        new_data["shelfobject"] = 15
        new_data["equipment_price"] = ""
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        self.assertTrue(
            json.loads(response.content)["equipment_price"][0]
            == _("A valid number is required.")
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_shelfobject_invalid_date(self):

        new_data = self.data.copy()
        new_data["shelfobject"] = 15
        new_data.update({"first_date_use": "12/23/2024"})
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        self.assertTrue(
            json.loads(response.content)["first_date_use"][0]
            == _(
                "Date has wrong format. Use one of these formats instead: DD/MM/YYYY, YYYY-MM-DD, DD/MM/YY."
            )
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_shelfobject_user_forbidden(self):
        self.client.logout()
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=self.data, content_type="application/json")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            json.loads(response.content)["detail"]
            == _("Authentication credentials were not provided.")
        )

    def test_edit_shelfobject_empty_status(self):

        new_data = self.data.copy()
        new_data["status"] = ""
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        self.assertTrue(
            json.loads(response.content)["status"][0]
            == _("This field may not be null.")
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_shelfobject_without_status(self):

        new_data = self.data.copy()
        del new_data["status"]
        url = reverse(
            "laboratory:api-shelfobject-edit-equipment-shelfobject",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.pk, "pk": 15},
        )
        response = self.client.put(url, data=new_data, content_type="application/json")
        self.assertTrue(
            json.loads(response.content)["status"][0] == _("This field is required.")
        )
        self.assertEqual(response.status_code, 400)
