"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
"""

# Import functions of another modules
from django.urls import path

from .views import index_sga, label_creator, get_sga_editor_options, information_creator, template, editor, \
    render_pdf_view

from django.conf.urls import url, include
from ajax_select import urls as ajax_select_urls
from . import views

# SGA
app_name = 'sga'

# Views
urlpatterns = [
    # sga/index_sga/
    path('index_sga', index_sga, name='index_sga'),
    # sga/label_information/
    path('information', information_creator, name='information'),
    # sga/label_template/
    path('label_editor_builder/<str:sustancetype>', template, name='template'),
    path('sga_editor_options', get_sga_editor_options, name='get_sga_editor_options'),
    path('show_editor_preview/<int:pk>', views.show_editor_preview, name='show_editor_preview'),
    # sga/label_creator/
    path('label_creator/<int:pk>', label_creator, name='label_creator'),
    # Django Ajax Selects
    url(r'^ajax_select/', include(ajax_select_urls)),
    path('search_autocomplete_sustance', views.search_autocomplete_sustance, name='search_autocomplete_sustance'),
    path('label_information', views.label_information, name='label_information'),
    path('label_template', views.label_template, name='label_template'),

    path('label_editor', views.label_editor, name='label_editor'),
    # sga/editor
    url(r'editor', editor, name='editor'),
    url(r'recipient_size/(?P<is_template>\d+)/(?P<pk>\d+)?$', views.get_recipient_size, name='get_recipient_size'),
    url(r'label_substance/(?P<pk>\d+)$', views.get_label_substance, name='get_label_substance'),
    url(r'get_preview/(?P<pk>\d+)$', views.get_preview, name='get_preview'),
    url(r'get_svgexport/(?P<is_pdf>\d+)/(?P<pk>\d+)$', views.get_svgexport, name='get_svgexport'),

    url(r'download/', render_pdf_view, name='download'),
    # sga/prudence
    path('prudence', views.get_prudence_advice, name='prudence'),
    # sga/get_danger_indication
    path('danger', views.get_danger_indication, name='get_danger_indication'),
    # sga/get_get_templateList
    url(r'getList', views.getTemplates, name='getList'),

    url(r'add_personal', views.create_personal_template, name='add_personal'),
    url(r'edit_personal/(?P<pk>\d+)$', views.edit_personal_template, name='edit_personal'),
    url(r'show_personal/(?P<pk>\d+)$', views.show_preview, name='show_personal'),

    url(r'getData', views.delete_personal, name='getData'),
    url(r'get_pdf/(?P<pk>\d+)$', views.render_user_pdf, name='get_pdf'),
    url(r'get_images', views.get_files, name='get_images'),
    url(r'add_substance', views.create_substance, name='add_substance'),
    url(r'add_recipient_size', views.create_recipient, name='add_recipient_size'),

]