from django.contrib.admin.models import ADDITION
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import Profile
from laboratory.utils import organilab_logentry
from pending_tasks.models import PendingTask
from report.utils import create_notification


def create_pending_task(
    created_by,
    name,
    rols,
    description="",
    status=PendingTask.PENDING,
    profile=None,
    link="",
    notify=False,
):
    pending_task = PendingTask.objects.create(
        created_by=created_by,
        name=name,
        description=description,
        status=status,
        profile=profile,
        link=link,
    )
    pending_task.rols.add(*rols)

    organilab_logentry(
        created_by,
        pending_task,
        ADDITION,
        changed_data=["name", "description", "status", "profile", "link"],
    )

    if notify:
        notify_task_created(pending_task, created_by)

    return pending_task


def notify_task_created(task, created_by):
    url = reverse("pending_tasks:view_task")
    message = _("New pending task: %s") % task.name

    users_to_notify = set()

    if task.profile_id and task.profile.user_id:
        users_to_notify.add(task.profile.user_id)

    role_user_ids = Profile.objects.filter(
        profilepermission__rol__in=task.rols.all()
    ).values_list("user_id", flat=True)
    users_to_notify.update(role_user_ids)
    users_to_notify.discard(created_by.pk)

    User = get_user_model()
    for user in User.objects.filter(pk__in=users_to_notify):
        create_notification(user, message, url)
