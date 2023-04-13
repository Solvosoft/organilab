from django.http import Http404
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from laboratory.models import LaboratoryRoom, OrganizationStructure, Furniture, Laboratory
from laboratory.utils import get_laboratories_from_organization, get_laboratories_from_organization_profile, \
    get_users_from_organization
from report.forms import RelOrganizationForm, RelLaboratoryForm, RelOrganizationLaboratoryForm, OrganizationForm
from django.contrib.auth.models import User

class GPaginatorMoreElements(GPaginator):
    page_size = 50

@register_lookups(prefix="labroombase", basename="labroombase")
class LabRoomModelLookups(generics.RetrieveAPIView, BaseSelect2View):
    model = LaboratoryRoom
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    organization, laboratory, all_labs_org = None, None, None

    def get_queryset(self):
        queryset = super().get_queryset()
        result = queryset.none()

        if self.laboratory:
            result = queryset.filter(laboratory=self.laboratory[0])

        if self.all_labs_org is not None:
            if self.all_labs_org:
                labs = get_laboratories_from_organization(self.organization.pk)
                result = queryset.filter(laboratory__in=labs)
        return result

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])
                self.laboratory = form.cleaned_data['laboratory']
                self.all_labs_org = form.cleaned_data['all_labs_org']
        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)


@register_lookups(prefix="furniturebase", basename="furniturebase")
class FurnitureModelLookups(generics.RetrieveAPIView, BaseSelect2View):
    model = Furniture
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    laboratory = None


    def get_queryset(self):
        queryset = super().get_queryset()
        result = queryset.none()
        if self.laboratory:
            lab_room = LaboratoryRoom.objects.filter(laboratory__in=self.laboratory)
            result = queryset.filter(labroom__in=lab_room)
        return result

    def list(self, request, *args, **kwargs):
        if self.laboratory is None:
            form = RelLaboratoryForm(self.request.GET)
            if form.is_valid():
                self.laboratory = form.cleaned_data['laboratory']
        if self.laboratory is None:
            raise Http404("Laboratory not found")
        return super().list(request, *args, **kwargs)

@register_lookups(prefix="laboratorybase", basename="laboratorybase")
class LaboratoryModelLookups(BaseSelect2View):
    model = Laboratory
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    organization= None

    def get_queryset(self):
        queryset = super().get_queryset()
        labs = queryset.none()

        if self.request.user is not None:
            if self.request.user:
                labs = get_laboratories_from_organization_profile(self.organization.pk, self.request.user.pk)
        return labs

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationLaboratoryForm(self.request.GET)

            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])
        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)

@register_lookups(prefix="usersbase", basename="usersbase")
class UserModelLookups(BaseSelect2View):
    model = User
    fields = ['first_name','last_name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    organization, all_labs_org= None, None

    def get_queryset(self):
        queryset = super().get_queryset()
        users = queryset.none()

        if self.all_labs_org is not None or self.request.user is not None:
            if self.all_labs_org or self.request.user:
                users = get_users_from_organization(self.organization.pk)
        return users

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = OrganizationForm(self.request.GET)

            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])

        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)
