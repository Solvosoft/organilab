# encoding: utf-8

'''
Created on 29 jun. 2018

@author: luisza
'''

from django.conf.urls import url
from .views import get_list_msds
urlpatterns = [
    url(r'^list$', get_list_msds, name="list_msds"),

]
