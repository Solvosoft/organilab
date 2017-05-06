'''
Created on 5 may. 2017

@author: luis
'''

from ajax_select import register, LookupChannel
from .models import Object
from django.db.models.query_utils import Q


@register('objects')
class TagsLookup(LookupChannel):

    model = Object

    def get_query(self, q, request):      
        return self.model.objects.filter(Q(code__icontains=q) | Q(
            name__icontains=q)|Q(cas_id_number__icontains=q)).order_by('name')[:8]

    def format_item_display(self, item):
        return u"<span class='tag'>(%s) %s</span>" % (item.code, item.name)