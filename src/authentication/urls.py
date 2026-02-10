# encoding: utf-8

"""
Created on 20 jun. 2018

@author: luisza
"""
from django.urls import path

from authentication import views

urlpatterns = [
    path(
        "permission_denied",
        views.PermissionDeniedView.as_view(),
        name="permission_denied",
    ),
]
