from django.contrib.auth.decorators import permission_required
from laboratory.models import Provider, Laboratory
from laboratory.forms import ProviderForm
from django.shortcuts import render, get_object_or_404
from auth_and_perms.organization_utils import user_is_allowed_on_organization


@permission_required("laboratory.view_provider")
def provider_view(request, org_pk=0, lab_pk=0):
    user_is_allowed_on_organization(request.user, org_pk)
    lab = get_object_or_404(Laboratory, pk=lab_pk)

    return render(
        request,
        "laboratory/provider_list.html",
        context={
            "laboratory": lab_pk,
            "org_pk": org_pk,
            "lab_pk": lab_pk,
            "form_create": ProviderForm(prefix="create", render_type="as_p"),
            "form_update": ProviderForm(prefix="update", render_type="as_p"),
        },
    )
