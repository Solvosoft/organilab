'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.conf.urls import url
from .views import index_printOrderManager, get_list_printObject, index_printManager, PrintLogin, PrintRegister, delete_print_byId, index_printManageById, contacts_printManageById, get_list_contactByPrint
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
    url(r'index_printManageById/(?P<pk>\d+)$', index_printManageById,
        name='index_printManageById'),
    url(r'contacts_printManageById/(?P<pk>\d+)$', contacts_printManageById,
        name='contacts_printManageById'),
    url(r'^listContactByPrint$', get_list_contactByPrint,
        name="list_contactByPrint"),
    # Methods in URL
    # Delete Print Object
    url(r'^printDelete$', delete_print_byId,
        name='printDelete'),
]
