from django.contrib.admin.models import ADDITION

from laboratory.utils import organilab_logentry
from pending_tasks.models import PendingTask


def create_pending_task(created_by, rols, organization=None, description="", status=PendingTask.PENDING, profile=None, link=""):
    pending_task = PendingTask.objects.create(
        organization=organization,
        created_by=created_by,
        description=description,
        status=status,
        profile=profile,
        link=link)
    pending_task.rols.add(*rols)

    changed_data = ['organization', 'created_by', 'description', 'status', 'profile', 'link']
    organilab_logentry(created_by, pending_task, ADDITION, changed_data=changed_data)

    return pending_task
