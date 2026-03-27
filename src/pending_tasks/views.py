from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required

from pending_tasks.forms import PendingTaskForm


@login_required
@permission_required("pending_tasks.view_pendingtask", raise_exception=True)
def view_task(request, org_pk=None):
    context = {
        "org_pk": org_pk,
        "create_form": PendingTaskForm(prefix="create", org_pk=org_pk),
        "update_form": PendingTaskForm(prefix="update", org_pk=org_pk),
    }
    return render(request, "tasks/tasks-view.html", context=context)
