from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
@permission_required("laboratory.add_organizationstructure", raise_exception=True)
def approvals_view(request):
    return render(request, "laboratory/approvals.html")