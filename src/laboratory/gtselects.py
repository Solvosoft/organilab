from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups

from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.forms import ValidateShelfForm
from laboratory.models import Object, OrganizationStructure
from auth_and_perms.models import Rol
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from laboratory.utils import get_pk_org_ancestors


@register_lookups(prefix="rol", basename="rolsearch")
class RolGModelLookup(BaseSelect2View):
    model = Rol
    fields = ['name']

@register_lookups(prefix="object", basename="objectsearch")
class ObjectGModelLookup(BaseSelect2View):
    model = Object
    fields = ['code', 'name']


@register_lookups(prefix="objectorgsearch", basename="objectorgsearch")
class ObjectGModelLookup(generics.RetrieveAPIView, BaseSelect2View):
    model = Object
    fields = ['code', 'name']
    org_pk = None
    shelf = None
    shelfobjet_type=None
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.shelf and self.shelf.limit_only_objects and self.shelfobjet_type:
            return self.shelf.available_objects_when_limit.filter(type=self.shelfobjet_type)

        queryset = super().get_queryset()
        if self.org_pk and self.shelfobjet_type:
            organizations = get_pk_org_ancestors(self.org_pk.pk)
            queryset = queryset.filter(organization__in=organizations,type=self.shelfobjet_type)
        else:
            queryset = queryset.none()
        return queryset

    def retrieve(self, request, pk, **kwargs):

        self.org_pk=get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)
        user_is_allowed_on_organization(request.user, self.org_pk)
        form = ValidateShelfForm(request.GET)
        if form.is_valid():
            shelf = form.cleaned_data['shelf']
            if organization_can_change_laboratory(shelf.furniture.labroom.laboratory, self.org_pk):
                self.shelf=shelf
                self.shelfobjet_type=form.cleaned_data['objecttype']

        return self.list(request, pk, **kwargs)



@register_lookups(prefix="userbase", basename="userbase")
class User(BaseSelect2View):
    model = User
    fields = ['username']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


