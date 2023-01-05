from django.shortcuts import get_object_or_404
from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups
from laboratory.models import Object, OrganizationStructure
from auth_and_perms.models import Rol
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

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
    organization = None
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset = queryset.filter(organization=self.organization)
        else:
            queryset = queryset.none()
        return queryset

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if not args:
            raise
        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)



@register_lookups(prefix="userbase", basename="userbase")
class User(BaseSelect2View):
    model = User
    fields = ['username']



