'''
Created on 3/15/2018

@author: migue56
'''

from django.conf.urls import url, include
from rest_framework.authtoken import views

from .reactive import ReactiveMolecularFormulaAPIView
from .views import (LaboratoryRoomAPIView,
                    FurnitureAPIView,
                    ShelfAPIView,
                    ShelfObjectAPIView,
                    ObjectAPIView
                    )
app_name = 'api'


# TOKEN URLs[
urlpatterns = [url(r'^token-auth/$', views.obtain_auth_token, name='get_auth_token')

               ]


# API URLs
room_api_urls = [
    url(r'^$', LaboratoryRoomAPIView.as_view(), name='api_laboratoryroom'),
    url(r'^(?P<pk>\d+)/$', LaboratoryRoomAPIView.as_view(),
        name='api_laboratoryroom_updates'),
]
furniture_api_urls = [
    url(r'^$', FurnitureAPIView.as_view(), name='api_furniture'),
    url(r'^(?P<pk>\d+)/$', FurnitureAPIView.as_view(),
        name='api_furniture_updates'),
]

shelf_api_urls = [
    url(r'^$', ShelfAPIView.as_view(), name='api_shelf'),
    url(r'^(?P<pk>\d+)/$', ShelfAPIView.as_view(), name='api_shelf_updates'),
]

shelfobject_api_urls = [
    url(r'^$', ShelfObjectAPIView.as_view(), name='api_shelfobject'),
    url(r'^(?P<pk>\d+)/$', ShelfObjectAPIView.as_view(),
        name='api_shelfobject_updates'),
]

object_api_urls = [
    url(r'reactive/name/', ReactiveMolecularFormulaAPIView.as_view(), name="api_molecularname"),
    url(r'^$', ObjectAPIView.as_view(), name='api_object'),
    url(r'^(?P<pk>\d+)/$', ObjectAPIView.as_view(), name='api_object_updates'),
]
# Main api urls
urlpatterns += [url(r'^(?P<lab_pk>\d+)/rooms/', include(room_api_urls)),
                url(r'^(?P<lab_pk>\d+)/furniture/',
                    include(furniture_api_urls)),
                url(r'^(?P<lab_pk>\d+)/shelf/', include(shelf_api_urls)),
                url(r'^(?P<lab_pk>\d+)/shelfobject/',
                    include(shelfobject_api_urls)),
                url(r'^(?P<lab_pk>\d+)/object/', include(object_api_urls)),
                ]
