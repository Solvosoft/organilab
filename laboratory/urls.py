'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from django.conf.urls import url
from laboratory.generic import ShelfCreate, ShelfDelete, ShelfListView
from laboratory.ajax_view import FurnitureCreate,list_shelf, list_shelf_render, ShelvesCreate

urlpatterns = [
    url(r"^create$", FurnitureCreate.as_view(),
        name="furniture_create"),
]

urlpatterns += [
    url(r"^shelf/list$", list_shelf, 
        name="shelf_list"),
    url(r"^shelf/create$", ShelfCreate.as_view(), 
        name="shelf_create")
]
