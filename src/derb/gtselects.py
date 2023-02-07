from django.shortcuts import get_object_or_404
from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups

from derb.models import CustomForm
from laboratory.models import Object, OrganizationStructure
from auth_and_perms.models import Rol
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from laboratory.utils import get_pk_org_ancestors


@register_lookups(prefix="informtemplate", basename="informtemplate")
class CustomFormModelLookup(generics.RetrieveAPIView, BaseSelect2View):
    model = CustomForm
    fields = ['name']
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
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        self.org_pk = self.organization.pk
        return self.list(request, pk, **kwargs)


