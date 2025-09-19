# encoding: utf-8

"""
Free as freedom will be 26/8/2016

@author: luisza
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from .utils import get_pk_org_ancestors_decendants
from .views.djgeneric import ListView
from laboratory.models import ShelfObject, Laboratory, OrganizationStructure
from laboratory.forms import (
    ReservedModalForm,
    TransferObjectForm,
    AddObjectForm,
    SubtractObjectForm,
)
from laboratory.forms import ReservationModalForm
from djgentelella.decorators.perms import any_permission_required


@method_decorator(login_required, name="dispatch")
@method_decorator(
    any_permission_required(
        ["laboratory.can_manage_disposal", "laboratory.can_view_disposal"]
    ),
    name="dispatch",
)
class SearchDisposalObject(ListView):
    model = ShelfObject
    search_fields = ["object__code", "object__name", "object__description"]
    template_name = "laboratory/disposal_substance.html"

    def get_queryset(self):
        user = self.request.user
        labs = Laboratory.objects.filter(
            profile__user=user.pk,
            organization=self.org,
            laboratoryroom__furniture__shelf__discard=True,
        ).distinct()

        return labs

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)

        return context
