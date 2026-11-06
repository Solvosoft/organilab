from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from laboratory.utils import check_user_access_kwargs_org_lab


@login_required
def lab_index(request, org_pk, lab_pk):
    # Este chequeo ya exige que la organización exista y que el laboratorio
    # esté entre los suyos; no hace falta repetirlo aquí.
    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404("")

    return render(
        request, "laboratory/index.html", {"laboratory": int(lab_pk), "org_pk": org_pk}
    )
