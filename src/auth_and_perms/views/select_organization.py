from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from auth_and_perms.forms import OrgTreeForm, SearchObjByOrgForm


@login_required
def select_organization_by_user(request):
    context = {
        "orgtree_form": OrgTreeForm(),
        "searchobjbyorg_form": SearchObjByOrgForm(),
    }
    return render(request, "auth_and_perms/select_organization.html", context=context)
