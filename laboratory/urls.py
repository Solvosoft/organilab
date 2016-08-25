'''
Created on 1/8/2016

@author: nashyra
'''
from __future__ import unicode_literals
from laboratory.generic import ShelfCreate, ObjectCreate, LabroomCreate,FurnitureCreate
from laboratory.ajax_view import list_shelf, list_objectfeatures
from django.conf.urls import url
from django.urls import reverse_lazy

from laboratory.views import index
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^login$', auth_views.login, {'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^logout$', auth_views.logout, {'next_page': reverse_lazy('laboratory:index')}, name='logout')
] 

urlpatterns += [
    url(r"^furniture/create$", FurnitureCreate.as_view(),
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
