'''
Created on 1/15/2018

@author: migue56
'''
from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework.authtoken import views

# API URLs
urlpatterns = [ ]

# TOKEN URLs
urlpatterns += [
    url(r'^api-token-auth/', views.obtain_auth_token)
]