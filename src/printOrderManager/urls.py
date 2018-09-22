'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.conf.urls import url
from .views import index_printOrderManager, get_list_printObject, index_printManager, PrintLogin, PrintRegister
from printOrderManager.views import PrintObjectCRUD

# Fixed: Name of the variable changed
printObjectCRUD = PrintObjectCRUD()

urlpatterns = printObjectCRUD.get_urls() + [
    url(r'index_printOrderManager', index_printOrderManager,
        name='index_printOrderManager'),
    url(r'^list$', get_list_printObject, name="list_printObject"),
    url(r'index_printManager', index_printManager,
        name='index_printManager'),
    url(r'^printLogin$', PrintLogin.as_view(),
        name='printLogin'),
    url(r'^printRegister$', PrintRegister.as_view(),
        name='printRegister'),
]
