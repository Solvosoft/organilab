from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from auth_and_perms.models import Profile, Rol, ProfilePermission
from laboratory.models import OrganizationStructure
from pending_tasks.models import PendingTask


class PendingTaskAPITestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user, id_card='12345'
        )

        self.other_user = User.objects.create_user(
            username='otheruser', password='testpass123'
        )
        self.other_profile = Profile.objects.create(
            user=self.other_user, id_card='67890'
        )

        self.org = OrganizationStructure.objects.create(name='Test Org')

        self.rol = Rol.objects.create(name='Test Rol', color='#FFFFFF')
        pt_ct = ContentType.objects.get_for_model(PendingTask)
        perms = Permission.objects.filter(content_type=pt_ct)
        self.rol.permissions.add(*perms)

        org_ct = ContentType.objects.get_for_model(OrganizationStructure)
        self.pp = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=org_ct,
            object_id=self.org.pk
        )
        self.pp.rol.add(self.rol)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.task_assigned = PendingTask.objects.create(
            description='Assigned task',
            status=0,
            profile=self.profile,
            created_by=self.user,
            organization=self.org
        )
        self.task_assigned.rols.add(self.rol)

        self.task_unassigned = PendingTask.objects.create(
            description='Unassigned task with matching rol',
            status=0,
            profile=None,
            created_by=self.other_user,
            organization=self.org
        )
        self.task_unassigned.rols.add(self.rol)

        self.task_other = PendingTask.objects.create(
            description='Other user task',
            status=0,
            profile=self.other_profile,
            created_by=self.other_user,
            organization=self.org
        )

        self.list_url = reverse('pending_tasks:pending_tasks-list')
        self.create_url = reverse('pending_tasks:pending_tasks-create-task')

    def test_list_tasks_returns_assigned_and_matching_rol(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        task_ids = [t['id'] for t in data]
        self.assertIn(self.task_assigned.pk, task_ids)
        self.assertIn(self.task_unassigned.pk, task_ids)
        self.assertNotIn(self.task_other.pk, task_ids)

    def test_list_tasks_filter_by_status(self):
        self.task_assigned.status = 1
        self.task_assigned.save()
        response = self.client.get(self.list_url, {'status': 0})
        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        task_ids = [t['id'] for t in data]
        self.assertNotIn(self.task_assigned.pk, task_ids)
        self.assertIn(self.task_unassigned.pk, task_ids)

    def test_create_task(self):
        response = self.client.post(
            self.create_url,
            {'description': 'New task', 'rols': [], 'link': 'https://example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        task = PendingTask.objects.get(description='New task')
        self.assertEqual(task.profile, self.profile)
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.link, 'https://example.com')
        self.assertEqual(task.status, 0)

    def test_create_task_without_link(self):
        response = self.client.post(
            self.create_url,
            {'description': 'Task no link', 'rols': []},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        task = PendingTask.objects.get(description='Task no link')
        self.assertFalse(task.link)

    def test_create_task_without_description(self):
        response = self.client.post(
            self.create_url,
            {'rols': []},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        task = PendingTask.objects.filter(
            created_by=self.user, description__isnull=True
        ).first()
        self.assertIsNotNone(task)

    def test_update_task_status(self):
        url = reverse(
            'pending_tasks:pending_tasks-updated-task-status',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.patch(
            url, {'status': 1}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.task_assigned.refresh_from_db()
        self.assertEqual(self.task_assigned.status, 1)

    def test_update_task_status_to_finished(self):
        self.task_assigned.status = 1
        self.task_assigned.save()
        url = reverse(
            'pending_tasks:pending_tasks-updated-task-status',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.patch(
            url, {'status': 2}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.task_assigned.refresh_from_db()
        self.assertEqual(self.task_assigned.status, 2)

    def test_assign_unassigned_task(self):
        url = reverse(
            'pending_tasks:pending_tasks-task-assign',
            kwargs={'pk': self.task_unassigned.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.task_unassigned.refresh_from_db()
        self.assertEqual(self.task_unassigned.profile, self.profile)

    def test_assign_already_assigned_task_fails(self):
        url = reverse(
            'pending_tasks:pending_tasks-task-assign',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_unassign_pending_task(self):
        url = reverse(
            'pending_tasks:pending_tasks-task-unassign',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.task_assigned.refresh_from_db()
        self.assertIsNone(self.task_assigned.profile)

    def test_unassign_non_pending_task_fails(self):
        self.task_assigned.status = 1
        self.task_assigned.save()
        url = reverse(
            'pending_tasks:pending_tasks-task-unassign',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_delete_task(self):
        url = reverse(
            'pending_tasks:pending_tasks-detail',
            kwargs={'pk': self.task_assigned.pk}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            PendingTask.objects.filter(pk=self.task_assigned.pk).exists()
        )

    def test_unauthenticated_user_gets_empty_list(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 0)
