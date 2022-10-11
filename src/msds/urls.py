# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''
from django.urls import re_path

from .views import get_list_msds, index_msds, regulation_view, download_all_regulations
from msds.views import MSDSObjectCRUD

msdsobj = MSDSObjectCRUD()

urlpatterns = msdsobj.get_urls() + [
    re_path(r'index_msds', index_msds, name='index_msds'),
    re_path(r'^list$', get_list_msds, name="list_msds"),
    re_path(r'regulations$', regulation_view, name="regulation_docs"),
    re_path(r'regulations/download/all', download_all_regulations, name="download_all_regulations")

]
