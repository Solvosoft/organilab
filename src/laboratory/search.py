# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
''' 

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.utils.decorators import method_decorator

from .utils import get_pk_org_ancestors_decendants
from .views.djgeneric import ListView
from laboratory.models import ShelfObject, Laboratory, OrganizationStructure
from laboratory.forms import ObjectSearchForm, ReservedModalForm, TransferObjectForm, AddObjectForm, SubtractObjectForm
from laboratory.forms import ReservationModalForm
from djgentelella.decorators.perms import any_permission_required


@method_decorator(login_required, name='dispatch')
class SearchObject(ListView):
    model = ShelfObject
    search_fields = ['object__code', 'object__name', 'object__description']
    template_name = "laboratory/search.html"

    def get_queryset(self):
        user = self.request.user
        params = {}
        filter_lab = True
        if 'q' in self.request.GET:
            form = ObjectSearchForm(self.request.GET, org_pk=self.org, user=self.request.user)
            if form.is_valid():
                if 'q' in form.cleaned_data:
                    params = {'object__pk__in': form.cleaned_data['q']}
                filter_lab = not form.cleaned_data['all_labs']

        pks = get_pk_org_ancestors_decendants(user,self.org)

        #organizations = OrganizationStructure.os_manager.filter_user(user)
        # User have perm on that organization ?  else it use assigned User with direct relationship

        labs = Laboratory.objects.filter(profile__user=user.pk,organization__in=pks).distinct()

        query = self.model.objects.filter(shelf__furniture__labroom__laboratory__in=labs)

        if filter_lab:
            if 'lab_pk' in self.kwargs:
                query = query.filter(
                    shelf__furniture__labroom__laboratory=self.kwargs.get('lab_pk'))

        if params:
            query = query.filter(**params)
        else:
            query = query.none()
        return query

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        if 'lab_pk' in self.kwargs:
            lab_pk=int(self.kwargs.get('lab_pk'))
            context['laboratory'] = self.kwargs.get('lab_pk')
            context['tranfer_object_form'] = TransferObjectForm(users=self.request.user, lab_send=lab_pk,org=self.org)
            context['add_object_form'] = AddObjectForm(lab=lab_pk)
            context['subtract_object_form'] = SubtractObjectForm()

        context['q'] = self.request.GET.get('q', '')
        context['options'] = ['Reservation','Add','Transfer','Substract']
        context['options'] = ['Reservation','Add','Transfer','Substract']

        context['modal_form_reservation'] = ReservationModalForm()

        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(any_permission_required(['laboratory.can_manage_disposal','laboratory.can_view_disposal']), name='dispatch')
class SearchDisposalObject(ListView):
    model = ShelfObject
    search_fields = ['object__code', 'object__name', 'object__description']
    template_name = "laboratory/disposal_substance.html"

    def get_queryset(self):
        user = self.request.user
        labs = Laboratory.objects.filter(profile__user=user.pk,organization=self.org,
                                         rooms__furniture__shelf__discard=True).distinct()

        return labs

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)

        return context