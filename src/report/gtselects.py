from django.http import Http404
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from laboratory.models import LaboratoryRoom, Furniture
from laboratory.utils import get_laboratories_from_organization
from report.forms import RelOrganizationForm


class GPaginatorMoreElements(GPaginator):
    page_size = 100

@register_lookups(prefix="lab_room", basename="lab_room")
class LabRoomLookup(generics.RetrieveAPIView, BaseSelect2View):
    model = LaboratoryRoom
    fields = ['name']
    ordering = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    organization, laboratory, lab_room, all_labs_org = None, None, None, False

    def get_queryset(self):
        queryset = super().get_queryset()
        result = queryset.none()
        if self.organization:
            if self.all_labs_org:
                labs_by_org = get_laboratories_from_organization(self.organization)
                result = LaboratoryRoom.objects.filter(laboratory__in=labs_by_org)
            else:
                if self.laboratory:
                    result = queryset.filter(laboratory=self.laboratory)

            if self.lab_room:
                id_list = list(self.lab_room.values_list('pk', flat=True))
                self.selected = list(map(str, id_list))
        return result

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationForm(request.GET)
            if form.is_valid():
                self.organization = form.cleaned_data['organization']
                self.laboratory = form.cleaned_data['laboratory']
                self.all_labs_org = form.cleaned_data['all_labs_org']
                self.lab_room = form.cleaned_data['lab_room']
        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)

@register_lookups(prefix="furniture", basename="furniture")
class FurnitureLookup(generics.RetrieveAPIView, BaseSelect2View):
    model = Furniture
    fields = ['name']
    ref_field = 'labroom'
    ordering = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]