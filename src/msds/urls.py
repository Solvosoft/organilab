# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''
from django.urls import path

from .views import get_list_msds, index_msds, regulation_view, download_all_regulations
from msds.views import MSDSObjectCRUD

msdsobj = MSDSObjectCRUD()

urlpatterns = [
    path('index_msds/', index_msds, name='index_msds'),
    path('msdsobject/create/', msdsobj.create, name='msds_msdsobject_create'),
    path('msdsobject/<int:pk>/detail/', msdsobj.detail, name='msds_msdsobject_detail'),
    path('msdsobject/<int:pk>/update/', msdsobj.update, name='msds_msdsobject_update'),
    path('msdsobject/<int:pk>/delete/', msdsobj.delete, name='msds_msdsobject_delete'),
    path('list/', get_list_msds, name="list_msds"),


]

regulation_urlpath = [
    path('regulations/', regulation_view, name="regulation_docs"),
    path('regulations/download/all', download_all_regulations, name="download_all_regulations"),
    ]