from __future__ import unicode_literals

from django.views.generic.edit import CreateView, DeleteView
from laboratory.models import Shelf
from django.contrib.messages.api import success

from django.views.generic.list import ListView
from django.core.urlresolvers import reverse_lazy
from django.db.models.query import QuerySet

class ShelfCreate(CreateView):
    model = Shelf
    fields = '__all__'
    success_url = "/"
    
class ShelfDelete(DeleteView):
    model = Shelf
    fields = '__all__'
    success_url = reverse_lazy('shelf_list.html')
    
class ShelfListView(ListView):
    model = Shelf
    
    def get_queryset(self):
        queryset = ListView.get_queryset(self)
        queryset = queryset.filter(cantidad__gte=5)
        return queryset