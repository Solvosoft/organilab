'''
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
'''

# Import functions of another modules
from sga.views import index_sga, pre_editor
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from ajax_select import urls as ajax_select_urls
from . import views


# SGA
app_name = 'sga'

# Views "The Hard Way"
urlpatterns = [
    # sga/index_sga/
    url(r'index_sga', index_sga, name='index_sga'),
    # sga/pre_editor/
    url(r'pre_editor', pre_editor, name='pre_editor'),
    # Django Ajax Selects
    url(r'^ajax_select/', include(ajax_select_urls)),
    # sga/autocompleteSustance/
    url(r'^search_autocomplete_sustance/', views.search_autocomplete_sustance, name='search_autocomplete_sustance')
]
