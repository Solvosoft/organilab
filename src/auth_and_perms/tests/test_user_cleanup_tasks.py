from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from auth_and_perms.models import UserDeletionRequest
from auth_and_perms.tasks import (
    cancel_requests_of_active_users,
    delete_expired_users,
    enqueue_inactive_users,
    send_user_deletion_warnings,
)

SENTINEL = "centinela-test"


@override_settings(DELETED_USER_SENTINEL_USERNAME=SENTINEL, USER_INACTIVITY_DAYS=365, USER_DELETION_GRACE_DAYS=30, USER_DELETION_WARNING_DAYS=(8, 1))
class UserCleanupTasksTest(TestCase):
    def setUp(self):
        self.now = timezone.now()
        old = self.now - timedelta(days=400)
        self.sentinel = User.objects.create_user(SENTINEL, password="x", last_login=old)
        self.inactive = User.objects.create_user("inactivo", "inactivo@example.com", "x", last_login=old)
        self.never_logged = User.objects.create_user("nunca", "nunca@example.com", "x")
        User.objects.filter(pk=self.never_logged.pk).update(date_joined=old)
        self.active = User.objects.create_user("activo", "activo@example.com", "x", last_login=self.now)
        self.superuser = User.objects.create_superuser("super", "super@example.com", "x", last_login=old)

    def test_enqueues_only_inactive_regular_users_once(self):
        enqueue_inactive_users(self.now)
        enqueue_inactive_users(self.now)
        queued = set(UserDeletionRequest.objects.values_list("user__username", flat=True))
        self.assertEqual(queued, {"inactivo", "nunca"})
        request = UserDeletionRequest.objects.get(user=self.inactive)
        self.assertEqual(request.reason, UserDeletionRequest.INACTIVE)
        self.assertEqual(request.expiration_date, self.now + timedelta(days=30))

    def test_login_after_request_cancels_it(self):
        enqueue_inactive_users(self.now)
        User.objects.filter(pk=self.inactive.pk).update(last_login=timezone.now() + timedelta(minutes=1))
        cancel_requests_of_active_users()
        self.assertFalse(UserDeletionRequest.objects.filter(user=self.inactive).exists())
        self.assertTrue(UserDeletionRequest.objects.filter(user=self.never_logged).exists())

    @mock.patch("auth_and_perms.tasks.notify_user_deletion_warning")
    def test_warnings_are_sent_once_per_threshold(self, notify):
        request = UserDeletionRequest.objects.create(user=self.inactive, expiration_date=self.now + timedelta(days=30))
        self.assertEqual(send_user_deletion_warnings(self.now), 0)
        self.assertEqual(send_user_deletion_warnings(self.now + timedelta(days=22, hours=1)), 1)
        self.assertEqual(send_user_deletion_warnings(self.now + timedelta(days=23)), 0)
        self.assertEqual(send_user_deletion_warnings(self.now + timedelta(days=29, hours=1)), 1)
        request.refresh_from_db()
        self.assertEqual(request.warnings_sent, [8, 1])
        self.assertEqual(notify.call_count, 2)

    @mock.patch("auth_and_perms.user_merge.notify_user_deleted")
    def test_expired_requests_delete_users(self, notify):
        UserDeletionRequest.objects.create(user=self.inactive, expiration_date=self.now - timedelta(minutes=1))
        UserDeletionRequest.objects.create(user=self.never_logged, expiration_date=self.now + timedelta(days=5))
        self.assertEqual(delete_expired_users(self.now), 1)
        self.assertFalse(User.objects.filter(pk=self.inactive.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.never_logged.pk).exists())
