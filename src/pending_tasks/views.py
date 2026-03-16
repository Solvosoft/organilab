from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required("pending_tasks.view_pendingtask", raise_exception=True)
def view_task(request):
    context = {}

    return render(request, "tasks/tasks-view.html", context=context)
