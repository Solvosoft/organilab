# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''
from django.urls import re_path

from .views import get_list_msds, index_msds, regulation_view, download_all_regulations
from msds.views import MSDSObjectCRUD

msdsobj = MSDSObjectCRUD()

urlpatterns = [
    re_path(r'index_msds/', index_msds, name='index_msds'),
    re_path(r'msds/msdsobject/create$', msdsobj.create, name='msds_msdsobject_create'),
    re_path(r'msds/msdsobject/(?P<pk>\d+)/detail$', msdsobj.detail, name='msds_msdsobject_detail'),
    re_path(r'msds/msdsobject/(?P<pk>\d+)/update$', msdsobj.update, name='msds_msdsobject_update'),
    re_path(r'msds/msdsobject/(?P<pk>\d+)/delete$', msdsobj.delete, name='msds_msdsobject_delete'),
    re_path(r'^list/', get_list_msds, name="list_msds"),
    re_path(r'regulations$', regulation_view, name="regulation_docs"),
    re_path(r'regulations/download/all', download_all_regulations, name="download_all_regulations")

]