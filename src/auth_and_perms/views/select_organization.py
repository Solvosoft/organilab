from django.shortcuts import render
from auth_and_perms.forms import OrgTreeForm, SearchObjByOrgForm
from django.contrib.auth.decorators import permission_required, login_required


@login_required
def select_organization_by_user(request):
    context = {
        "orgtree_form": OrgTreeForm(),
        "searchobjbyorg_form": SearchObjByOrgForm(),
    }
    return render(request, "auth_and_perms/select_organization.html", context=context)

@login_required
@permission_required("risk_management.view_riskzone", raise_exception=True)
def map_of_laboratories_view(request, org_pk):
    return render(request, "auth_and_perms/map_of_laboratories.html", {"org_pk": org_pk})
