# encoding: utf-8

'''
Created on 20 jun. 2018

@author: luisza
'''
from django.urls import re_path

from authentication import views

urlpatterns = [

    re_path(r'^request_demo$', views.RequestDemoView.as_view(), name='request-demo'),
    re_path(r'^request_demo_done$', views.request_demo_done, name='request-demo-done'),

    re_path(r'^permission_denied$', views.PermissionDeniedView.as_view(), name='permission_denied'),
    re_path(r'^feedback$', views.FeedbackView.as_view(), name='feedback'),




]
