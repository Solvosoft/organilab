from django.http import Http404
from django.shortcuts import get_object_or_404
from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups
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
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.org_pk:
            organizations = get_pk_org_ancestors(self.org_pk)
            queryset = queryset.filter(organization__in=organizations)
        else:
            queryset = queryset.none()
        return queryset

    def retrieve(self, request, pk, **kwargs):
        try:
            self.org_pk=int(pk)
        except Exception as e:
            raise Http404("Not organization found")

        return self.list(request, pk, **kwargs)



@register_lookups(prefix="userbase", basename="userbase")
class User(BaseSelect2View):
    model = User
    fields = ['username']



