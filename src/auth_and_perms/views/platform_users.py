from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from auth_and_perms.forms import MergePlatformUserForm


@login_required
@permission_required("auth_and_perms.can_manage_users", raise_exception=True)
def platform_users(request):
    return render(request, "auth_and_perms/platform_users.html", context={"merge_form": MergePlatformUserForm()})
