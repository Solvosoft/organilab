from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from presentation.platform.forms import AlertRuleForm, NotificationSettingForm, SystemParameterForm


@login_required
@permission_required("presentation.view_systemparameter", raise_exception=True)
def systemparameter_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {"org_pk": org_pk, "form_update": SystemParameterForm(prefix="update")}
    return render(request, "platform/systemparameter_list.html", context=context)


@login_required
@permission_required("presentation.view_notificationsetting", raise_exception=True)
def notificationsetting_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {"org_pk": org_pk, "form_update": NotificationSettingForm(prefix="update")}
    return render(request, "platform/notificationsetting_list.html", context=context)


@login_required
@permission_required("presentation.view_alertrule", raise_exception=True)
def alertrule_list(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    context = {
        "org_pk": org_pk,
        "form_create": AlertRuleForm(prefix="create", user=request.user),
        "form_update": AlertRuleForm(prefix="update", user=request.user),
    }
    return render(request, "platform/alertrule_list.html", context=context)
