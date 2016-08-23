'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from django.conf.urls import url
from laboratory.generic import ShelfCreate, ShelfDelete, ShelfListView, ObjectCreate, LabroomCreate
from laboratory.ajax_view import FurnitureCreate,list_shelf, list_objectfeatures

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

urlpatterns += [
    url(r"^object/create$", ObjectCreate.as_view(), 
        name="object_create"),
    url(r"^objectfeatures/list$", list_objectfeatures, 
        name="objectfeatures_list"),
                
]

urlpatterns += [
    url(r"^laboratoryroom/create$", LabroomCreate.as_view(), 
        name="laboratoryroom_create"),
    url(r"^objectfeatures/list$", list_objectfeatures, 
        name="objectfeatures_list"),
]