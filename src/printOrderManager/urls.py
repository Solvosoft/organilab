'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.conf.urls import url, include
from .views import index_printOrderManager, get_list_printObject, index_printManager, PrintLogin, PrintRegister, delete_print_byId, index_printManageById, contacts_printManageById, get_list_contactByPrint, giveDropPermissionsById, createContact_printManageById, get_list_usersNotRelatedToPrint, createPaperType_printManageById
from printOrderManager.views import PrintObjectCRUD
# DJANGO REST FRAMEWORK
from rest_framework.routers import DefaultRouter
from printOrderManager.api import RequestLabelPrintViewSet, ContactViewSet, PrintObjectViewSet, PaperTypeViewSet
from rest_framework_jwt.views import obtain_jwt_token


# Fixed: Name of the variable changed
printObjectCRUD = PrintObjectCRUD()
# DJANGO REST FRAMEWORK
router = DefaultRouter()
router.register(r'printerorders', RequestLabelPrintViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'printObject', PrintObjectViewSet)
router.register(r'paperType', PaperTypeViewSet)


urlpatterns = printObjectCRUD.get_urls() + [
    url(r'index_printOrderManager', index_printOrderManager,
        name='index_printOrderManager'),
    url(r'^list_printObject$', get_list_printObject, name="list_printObject"),
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
    url(r'createContact_printManageById/(?P<pk>\d+)$', createContact_printManageById,
        name='createContact_printManageById'),
    url(r'createPaperType_printManageById/(?P<pk>\d+)$', createPaperType_printManageById,
        name='createPaperType_printManageById'),
    url(r'^listContactByPrint$', get_list_contactByPrint,
        name="list_contactByPrint"),
    # Methods in URL
    # Delete Print Object
    url(r'^printDelete$', delete_print_byId,
        name='printDelete'),
    # Give and drop permissions
    url(r'^giveDropPermissionsById$', giveDropPermissionsById,
        name='giveDropPermissionsById'),
    url(r'^list_usersNotRelatedToPrint$', get_list_usersNotRelatedToPrint,
        name="list_usersNotRelatedToPrint"),
    # DJANGO REST FRAMEWORK
    url('API/', include(router.urls)),
]
