from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from presentation.platform.forms import SystemParameterForm


@login_required
@permission_required("presentation.view_systemparameter", raise_exception=True)
def systemparameter_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {"org_pk": org_pk, "form_update": SystemParameterForm(prefix="update")}
    return render(request, "platform/systemparameter_list.html", context=context)
