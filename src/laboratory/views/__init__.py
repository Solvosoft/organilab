from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from laboratory.models import OrganizationStructure
from laboratory.utils import check_user_access_kwargs_org_lab


@login_required
def lab_index(request, org_pk, lab_pk):
    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404("")

    organization = OrganizationStructure.objects.filter(pk=org_pk).first()
    if not organization:
        raise Http404("Organization not found")

    # Verificar si el laboratorio pertenece a la organización actual o sus descendientes
    lab_ids = list(organization.get_my_laboratories)
    if lab_pk not in lab_ids:
        # Si no está en las hijas, verificar en los ancestros
        for ancestor in reversed(list(organization.ancestors())):
            ancestor_lab_ids = list(ancestor.get_my_laboratories)
            if lab_pk in ancestor_lab_ids:
                break
        else:
            raise Http404("Laboratory is not related to this organization")

    return render(
        request, "laboratory/index.html", {"laboratory": int(lab_pk), "org_pk": org_pk}
    )
