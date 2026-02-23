import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse

from auth_and_perms.models import Profile, Rol, ProfilePermission
from laboratory.models import OrganizationStructure
from pending_tasks.models import PendingTask
from pending_tasks.utils import create_pending_task

User = get_user_model()


def create_user_with_profile(username, password="pass1234"):
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(
        user=user,
        phone_number="",
        id_card="0-0000-0000",
        job_position="Test",
    )
    return user


class PendingTaskSetUpMixin:
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.filter(username="admin").first()
        self.org = OrganizationStructure.objects.first()
        self.client = Client()

        self.role = Rol.objects.create(name="Pending Task Role", color="#ABC")
        pending_task_ct = ContentType.objects.get(
            app_label="pending_tasks", model="pendingtask"
        )
        permissions = Permission.objects.filter(content_type=pending_task_ct)
        self.role.permissions.add(*permissions)

        self.user.user_permissions.add(*permissions)

        org_ct = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )
        self.profile_permission = ProfilePermission.objects.create(
            profile=self.user.profile,
            object_id=self.org.pk,
            content_type=org_ct,
        )
        self.profile_permission.rol.add(self.role)

        # Refetch user to clear Django's cached permissions
        self.user = User.objects.get(pk=self.user.pk)
        self.client.force_login(self.user)


class PendingTaskModelTest(PendingTaskSetUpMixin, TestCase):

    def test_status_constants(self):
        self.assertEqual(PendingTask.PENDING, 0)
        self.assertEqual(PendingTask.IN_PROCESS, 1)
        self.assertEqual(PendingTask.FINISHED, 2)

    def test_create_pending_task(self):
        task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Test task",
            status=PendingTask.PENDING,
        )
        task.rols.add(self.role)
        self.assertEqual(task.status, PendingTask.PENDING)
        self.assertEqual(task.description, "Test task")
        self.assertIn(self.role, task.rols.all())

    def test_str_representation(self):
        task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="My task",
            profile=self.user.profile,
        )
        self.assertEqual(str(task), f"My task - {self.user.profile}")

    def test_default_status_is_pending(self):
        task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Defaults",
        )
        self.assertEqual(task.status, PendingTask.PENDING)

    def test_profile_set_null_on_delete(self):
        other_user = create_user_with_profile("tempuser")
        task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="SET_NULL test",
            profile=other_user.profile,
        )
        other_user.profile.delete()
        task.refresh_from_db()
        self.assertIsNone(task.profile)

    def test_meta_ordering(self):
        self.assertEqual(PendingTask._meta.ordering, ['-creation_date'])

    def test_meta_verbose_name(self):
        self.assertEqual(str(PendingTask._meta.verbose_name), "Pending task")
        self.assertEqual(str(PendingTask._meta.verbose_name_plural), "Pending tasks")


class CreatePendingTaskUtilTest(PendingTaskSetUpMixin, TestCase):

    def test_create_pending_task_util(self):
        task = create_pending_task(
            created_by=self.user,
            rols=[self.role],
            organization=self.org,
            description="Util task",
            link="https://example.com",
        )
        self.assertEqual(task.description, "Util task")
        self.assertEqual(task.status, PendingTask.PENDING)
        self.assertEqual(task.organization, self.org)
        self.assertEqual(task.link, "https://example.com")
        self.assertIn(self.role, task.rols.all())

    def test_create_pending_task_with_profile(self):
        task = create_pending_task(
            created_by=self.user,
            rols=[self.role],
            organization=self.org,
            description="Assigned task",
            profile=self.user.profile,
        )
        self.assertEqual(task.profile, self.user.profile)

    def test_create_pending_task_custom_status(self):
        task = create_pending_task(
            created_by=self.user,
            rols=[self.role],
            organization=self.org,
            description="In process",
            status=PendingTask.IN_PROCESS,
        )
        self.assertEqual(task.status, PendingTask.IN_PROCESS)


class PendingTaskAPIListTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.task = create_pending_task(
            created_by=self.user,
            rols=[self.role],
            organization=self.org,
            description="Visible task",
            profile=self.user.profile,
        )
        self.list_url = reverse("pending_tasks:pending_tasks-list")

    def test_list_returns_200(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_task(self):
        response = self.client.get(self.list_url)
        data = json.loads(response.content)
        self.assertGreaterEqual(data["recordsTotal"], 1)

    def test_list_unauthenticated_returns_401_or_403(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [401, 403])

    def test_list_filters_by_profile(self):
        other_user = create_user_with_profile("otheruser")
        other_task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Other user task",
            profile=other_user.profile,
        )
        response = self.client.get(self.list_url)
        data = json.loads(response.content)
        task_ids = [t["id"] for t in data["data"]]
        self.assertIn(self.task.pk, task_ids)
        self.assertNotIn(other_task.pk, task_ids)

    def test_list_shows_tasks_by_role_when_no_profile(self):
        unassigned_task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Role-based task",
        )
        unassigned_task.rols.add(self.role)
        response = self.client.get(self.list_url)
        data = json.loads(response.content)
        task_ids = [t["id"] for t in data["data"]]
        self.assertIn(unassigned_task.pk, task_ids)

    def test_list_search_filter(self):
        response = self.client.get(self.list_url, {"search": "Visible"})
        data = json.loads(response.content)
        self.assertGreaterEqual(data["recordsFiltered"], 1)

    def test_list_status_filter(self):
        response = self.client.get(
            self.list_url, {"status": PendingTask.PENDING}
        )
        data = json.loads(response.content)
        for t in data["data"]:
            self.assertEqual(t["status"]["id"], PendingTask.PENDING)


class PendingTaskAPIDetailTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.task = create_pending_task(
            created_by=self.user,
            rols=[self.role],
            organization=self.org,
            description="Detail task",
            profile=self.user.profile,
        )

    def test_destroy_task(self):
        url = reverse(
            "pending_tasks:pending_tasks-detail", kwargs={"pk": self.task.pk}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(PendingTask.objects.filter(pk=self.task.pk).exists())

    def test_update_task(self):
        url = reverse(
            "pending_tasks:pending_tasks-detail", kwargs={"pk": self.task.pk}
        )
        data = {
            "description": "Updated description",
            "rols": [self.role.pk],
        }
        response = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.description, "Updated description")


class PendingTaskAssignTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Unassigned task",
            status=PendingTask.PENDING,
        )
        self.task.rols.add(self.role)

    def test_task_assign(self):
        url = reverse(
            "pending_tasks:pending_tasks-task-assign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.profile, self.user.profile)

    def test_task_assign_already_assigned(self):
        self.task.profile = self.user.profile
        self.task.save()
        url = reverse(
            "pending_tasks:pending_tasks-task-assign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_task_assign_unauthenticated(self):
        self.client.logout()
        url = reverse(
            "pending_tasks:pending_tasks-task-assign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        self.assertIn(response.status_code, [401, 403])


class PendingTaskUnassignTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Assigned task",
            status=PendingTask.PENDING,
            profile=self.user.profile,
        )
        self.task.rols.add(self.role)

    def test_task_unassign(self):
        url = reverse(
            "pending_tasks:pending_tasks-task-unassign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.profile)

    def test_task_unassign_not_assigned_to_user(self):
        other_user = create_user_with_profile("otherunassign")
        self.task.profile = other_user.profile
        self.task.save()
        url = reverse(
            "pending_tasks:pending_tasks-task-unassign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        # 404 because filter_queryset excludes tasks not visible to the user
        self.assertEqual(response.status_code, 404)

    def test_task_unassign_when_not_pending(self):
        self.task.status = PendingTask.IN_PROCESS
        self.task.save()
        url = reverse(
            "pending_tasks:pending_tasks-task-unassign",
            kwargs={"pk": self.task.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class PendingTaskUpdateStatusTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Status task",
            status=PendingTask.PENDING,
            profile=self.user.profile,
        )
        self.task.rols.add(self.role)

    def test_update_status_to_in_process(self):
        url = reverse(
            "pending_tasks:pending_tasks-updated-task-status",
            kwargs={"pk": self.task.pk},
        )
        data = {"status": PendingTask.IN_PROCESS}
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, PendingTask.IN_PROCESS)

    def test_update_status_to_finished(self):
        url = reverse(
            "pending_tasks:pending_tasks-updated-task-status",
            kwargs={"pk": self.task.pk},
        )
        data = {"status": PendingTask.FINISHED}
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, PendingTask.FINISHED)

    def test_update_status_invalid_value(self):
        url = reverse(
            "pending_tasks:pending_tasks-updated-task-status",
            kwargs={"pk": self.task.pk},
        )
        data = {"status": 99}
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_update_status_not_assigned_to_user(self):
        other_user = create_user_with_profile("otherstatus")
        self.task.profile = other_user.profile
        self.task.save()
        url = reverse(
            "pending_tasks:pending_tasks-updated-task-status",
            kwargs={"pk": self.task.pk},
        )
        data = {"status": PendingTask.IN_PROCESS}
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )
        # 404 because filter_queryset excludes tasks not visible to the user
        self.assertEqual(response.status_code, 404)

    def test_update_status_unauthenticated(self):
        self.client.logout()
        url = reverse(
            "pending_tasks:pending_tasks-updated-task-status",
            kwargs={"pk": self.task.pk},
        )
        data = {"status": PendingTask.IN_PROCESS}
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertIn(response.status_code, [401, 403])


class PendingTaskPermissionTest(PendingTaskSetUpMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.unprivileged_user = create_user_with_profile("noperm")
        self.task = PendingTask.objects.create(
            organization=self.org,
            created_by=self.user,
            description="Permission task",
            status=PendingTask.PENDING,
            profile=self.unprivileged_user.profile,
        )
        self.task.rols.add(self.role)

    def test_user_without_permissions_cannot_list(self):
        self.client.force_login(self.unprivileged_user)
        url = reverse("pending_tasks:pending_tasks-list")
        response = self.client.get(url)
        self.assertIn(response.status_code, [401, 403])

    def test_user_without_permissions_cannot_delete(self):
        self.client.force_login(self.unprivileged_user)
        url = reverse(
            "pending_tasks:pending_tasks-detail", kwargs={"pk": self.task.pk}
        )
        response = self.client.delete(url)
        self.assertIn(response.status_code, [401, 403])
