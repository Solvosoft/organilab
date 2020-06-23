# encoding: utf-8

'''
Created on 20 jun. 2018

@author: luisza
'''

from django.conf.urls import url

from authentication import views

urlpatterns = [

    url(r'^request_demo$', views.RequestDemoView.as_view(), name='request-demo'),
    url(r'^request_demo_done$', views.request_demo_done, name='request-demo-done'),

    url(r'^permission_denied$', views.PermissionDeniedView.as_view(), name='permission_denied'),
    url(r'^feedback$', views.FeedbackView.as_view(), name='feedback'),




]
