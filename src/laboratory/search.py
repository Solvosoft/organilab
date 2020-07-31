# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
''' 

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.contrib.auth.models import User

from laboratory.models import ShelfObject, Laboratory, OrganizationStructure
from laboratory.forms import ObjectSearchForm
from babel.util import distinct


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
            form = ObjectSearchForm(self.request.GET)
            if form.is_valid():
                if 'q' in form.cleaned_data:
                    params = {'object__pk__in': form.cleaned_data['q']}
                filter_lab = not form.cleaned_data['all_labs']

        organizations = OrganizationStructure.os_manager.filter_user(user)
        # User have perm on that organization ?  else it use assigned User with direct relationship
        if not organizations:    
             organizations=[]
        labs = Laboratory.objects.filter(Q(profile__user=user.pk) |
                                      Q (organization__in=organizations) 
                                      ).distinct()
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
            context['laboratory'] = self.kwargs.get('lab_pk')
        context['q'] = self.request.GET.get('q', '')
        return context
