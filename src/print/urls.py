'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.conf.urls import url
from .views import index_print
# from msds.views import MSDSObjectCRUD

urlpatterns = [
    url(r'index_print', index_print, name='index_print'),
]
