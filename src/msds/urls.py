# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''

from django.conf.urls import url
from .views import get_list_msds, organilab_tree, index_msds, regulation_view, download_all_regulations
from msds.views import MSDSObjectCRUD

msdsobj = MSDSObjectCRUD()

urlpatterns = msdsobj.get_urls() + [
    url(r'index_msds', index_msds, name='index_msds'),
    url(r'^organilab/tree', organilab_tree, name='organilab_tree'),
    url(r'^list$', get_list_msds, name="list_msds"),
    url(r'regulations$', regulation_view, name="regulation_docs"),
    url(r'regulations/download/all', download_all_regulations, name="download_all_regulations")

]
