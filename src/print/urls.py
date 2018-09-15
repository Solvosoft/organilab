'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.conf.urls import url
from .views import index_print, get_list_print
from print.views import PrintCRUD

print = PrintCRUD()

urlpatterns = print.get_urls() + [
    url(r'index_print', index_print, name='index_print'),
    url(r'^list$', get_list_print, name="list_print"),
]
