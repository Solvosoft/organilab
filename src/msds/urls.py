# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''

from django.conf.urls import url
from .views import get_list_msds
from msds.views import MSDSObjectCRUD

msdsobj = MSDSObjectCRUD()

urlpatterns = msdsobj.get_urls() + [
    url(r'^list$', get_list_msds, name="list_msds"),

]
