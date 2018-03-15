'''
Created on 1/15/2018

@author: migue56
'''
from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework.authtoken import views


from .views import LaboratoryRoomAPIView

app_name = 'api'


# TOKEN URLs[
urlpatterns = [url(r'^token-auth/$', views.obtain_auth_token, name='get_auth_token')
               
]


# API URLs
room_api_urls = [
        url(r'^$',LaboratoryRoomAPIView.as_view(),name='api_laboratoryroom'),
        url(r'^(?P<pk>\d+)/$',LaboratoryRoomAPIView.as_view(),name='api_laboratoryroom_updates'),
    ]



urlpatterns += [url(r'^(?P<lab_pk>\d+)/rooms/', include(room_api_urls)),
                
                ]