from django.http import Http404
from django.shortcuts import render
from django_ajax.decorators import ajax
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
import json

from laboratory.utils import check_user_access_kwargs_org_lab


@login_required
def lab_index(request, org_pk, lab_pk):
    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404()

    return render(
        request, "laboratory/index.html", {"laboratory": int(lab_pk), "org_pk": org_pk}
    )
