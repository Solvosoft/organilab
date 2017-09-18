'''
Created on 5 may. 2017

@author: luis
'''

from ajax_select import register, LookupChannel
from .models import Object
from django.contrib.auth.models import User
from django.db.models.query_utils import Q



@register('objects')
class TagsLookup(LookupChannel):

    model = Object

    def get_query(self, q, request):
        return self.model.objects.filter(Q(code__icontains=q) | Q(
            name__icontains=q)|Q(cas_id_number__icontains=q)).order_by('name')[:8]

    def format_item_display(self, item):
        return u"<span class='tag'>(%s) %s</span>" % (item.code, item.name)

#Buscar usuarios
@register('users')
class UserLookup(LookupChannel):
    model = User

    def get_query(self, q, request):
        qs = q.split(' ')
        _filter = None
        for nq in qs:
            if _filter is None:
                _filter = Q(username__icontains=nq) | Q(first_name__icontains=nq) | Q(last_name__icontains=nq)
            else:
                _filter |= Q(username__icontains=nq) | Q(first_name__icontains=nq) | Q(last_name__icontains=nq)

        return self.model.objects.filter(_filter).order_by('username')[:8]

    def format_item_display(self, item):
        return u"<span class='tag'>(%s) %s</span>" % (item.username, item.get_full_name())
