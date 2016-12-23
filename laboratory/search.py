# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from __future__ import unicode_literals
from django.views.generic.list import ListView
from laboratory.models import ShelfObject
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class SearchObject(ListView):
    model = ShelfObject
    search_fields = ['object__code', 'object__name', 'object__description']
    template_name = "laboratory/search.html"

    def get_queryset_params(self):
        params = None
        if 'q' in self.request.GET:
            q = str(self.request.GET.get('q'))
            for field in self.search_fields:
                if params:
                    params |= Q(**{field + "__icontains": q})
                else:
                    params = Q(**{field + "__icontains": q})

        return params

    def get_queryset(self):
        query = ListView.get_queryset(self)
        if 'lab_pk' in self.kwargs:
            query = query.filter(shelf__furniture__labroom__laboratory=self.kwargs.get('lab_pk'))
        params = self.get_queryset_params()
        if params:
            query = query.filter(params)
        else:
            query = query.none()
        return query
