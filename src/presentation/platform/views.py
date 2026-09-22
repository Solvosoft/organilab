from functools import wraps

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from auth_and_perms.organization_utils import organization_permissions, user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from presentation.platform.forms import AlertRuleForm, NotificationSettingForm, SystemParameterForm


def organization_permission_required(perm):
    """Como ``permission_required``, pero el permiso tiene que venir de un rol de la organización."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, org_pk, *args, **kwargs):
            organization = get_object_or_404(OrganizationStructure, pk=org_pk)
            user_is_allowed_on_organization(request.user, organization)
            if perm not in organization_permissions(request.user, organization):
                raise PermissionDenied
            return view(request, org_pk, *args, **kwargs)

        return wrapper

    return decorator


@login_required
@permission_required("presentation.view_systemparameter", raise_exception=True)
@organization_permission_required("presentation.view_systemparameter")
def systemparameter_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {"org_pk": org_pk, "form_update": SystemParameterForm(prefix="update")}
    return render(request, "platform/systemparameter_list.html", context=context)


@login_required
@permission_required("presentation.view_notificationsetting", raise_exception=True)
@organization_permission_required("presentation.view_notificationsetting")
def notificationsetting_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {"org_pk": org_pk, "form_update": NotificationSettingForm(prefix="update")}
    return render(request, "platform/notificationsetting_list.html", context=context)


@login_required
@permission_required("presentation.view_alertrule", raise_exception=True)
@organization_permission_required("presentation.view_alertrule")
def alertrule_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        "org_pk": org_pk,
        "form_create": AlertRuleForm(prefix="create", user=request.user),
        "form_update": AlertRuleForm(prefix="update", user=request.user),
    }
    return render(request, "platform/alertrule_list.html", context=context)
