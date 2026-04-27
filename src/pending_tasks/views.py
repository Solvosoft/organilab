from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required

from pending_tasks.forms import PendingTaskForm


@login_required
@permission_required("pending_tasks.view_pendingtask", raise_exception=True)
def view_task(request):
    context = {
        "create_form": PendingTaskForm(prefix="create"),
        "update_form": PendingTaskForm(prefix="update"),
    }
    return render(request, "tasks/tasks-view.html", context=context)
