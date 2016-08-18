'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.conf.urls import url
from laboratory.generic import ShelfCreate, ShelfDelete, ShelfListView
#from reporter.ajax_view import list_proveedor, ProveedorCreate

urlpatterns = [
               url(r"^create$", ShelfCreate.as_view(),
                   name="shelf_create"),
               url(r"^list$", ShelfListView.as_view(),
                   name="shelf_list"),
               url(r"^delete/(?P<pk>\d+)$", ShelfDelete.as_view(),
                   name="shelf_confirm_delete")
]