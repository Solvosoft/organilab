import importlib
import logging
import math
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.utils import timezone

from auth_and_perms.models import UserDeletionRequest
from auth_and_perms.user_merge import UserManagementError, delete_user
from auth_and_perms.user_notifications import notify_user_deletion_warning

app = importlib.import_module(settings.CELERY_MODULE).app
logger = logging.getLogger("organilab")


def enqueue_inactive_users(now=None):
    """Programa la eliminación de quien no inicia sesión hace USER_INACTIVITY_DAYS días."""
    now = now or timezone.now()
    limit = now - timedelta(days=settings.USER_INACTIVITY_DAYS)
    users = (
        User.objects.filter(is_superuser=False, deletion_request__isnull=True)
        .filter(Q(last_login__lt=limit) | Q(last_login__isnull=True, date_joined__lt=limit))
        .exclude(username=settings.DELETED_USER_SENTINEL_USERNAME)
    )
    expiration = now + timedelta(days=settings.USER_DELETION_GRACE_DAYS)
    requests = [UserDeletionRequest(user=user, reason=UserDeletionRequest.INACTIVE, expiration_date=expiration) for user in users]
    UserDeletionRequest.objects.bulk_create(requests, ignore_conflicts=True)
    return len(requests)


def cancel_requests_of_active_users():
    """Quien volvió a iniciar sesión después de programarse ya no se elimina."""
    return UserDeletionRequest.objects.filter(user__last_login__gt=F("creation_date")).delete()[0]


def send_user_deletion_warnings(now=None):
    now = now or timezone.now()
    sent = 0
    for deletion_request in UserDeletionRequest.objects.filter(expiration_date__gt=now).select_related("user__profile"):
        days_left = math.ceil((deletion_request.expiration_date - now) / timedelta(days=1))
        due = [days for days in settings.USER_DELETION_WARNING_DAYS if days_left <= days and days not in deletion_request.warnings_sent]
        if not due:
            continue
        notify_user_deletion_warning(deletion_request, days_left)
        deletion_request.warnings_sent = sorted(set(deletion_request.warnings_sent) | set(due), reverse=True)
        deletion_request.save(update_fields=["warnings_sent"])
        sent += 1
    return sent


def delete_expired_users(now=None):
    now = now or timezone.now()
    deleted = 0
    for deletion_request in UserDeletionRequest.objects.filter(expiration_date__lte=now).select_related("user"):
        try:
            delete_user(deletion_request.user)
            deleted += 1
        except UserManagementError as e:
            logger.error("User %s could not be deleted: %s", deletion_request.user.username, e)
    return deleted


@app.task()
def manage_inactive_users():
    """Recorre el ciclo completo; cada paso es idempotente."""
    cancel_requests_of_active_users()
    enqueue_inactive_users()
    send_user_deletion_warnings()
    delete_expired_users()
