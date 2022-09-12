"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
"""

# Import functions of another modules
from django.urls import path

from .views import index_sga, template, editor, render_pdf_view

from django.conf.urls import url, include
from ajax_select import urls as ajax_select_urls
from . import views

# SGA
app_name = 'sga'

# Views
urlpatterns = [
    # sga/index_sga/
    path('index_sga', index_sga, name='index_sga'),
    path('label_editor_builder/<str:organilabcontext>/', template, name='template'),
    # Django Ajax Selects
    url(r'^ajax_select/', include(ajax_select_urls)),

    # sga/editor
    url(r'editor/(?P<organilabcontext>\w+)/', editor, name='editor'),
    url(r'recipient_size/(?P<organilabcontext>\w+)/(?P<is_template>\d+)/(?P<pk>\d+)?$', views.get_recipient_size, name='get_recipient_size'),
    url(r'label_substance/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.get_label_substance, name='get_label_substance'),
    url(r'get_preview/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.get_preview, name='get_preview'),
    url(r'get_svgexport/(?P<is_pdf>\d+)/(?P<pk>\d+)$', views.get_svgexport, name='get_svgexport'),

    url(r'download/', render_pdf_view, name='download'),
    # sga/prudence
    path('prudence/(?P<organilabcontext>\w+)', views.get_prudence_advice, name='prudence'),
    # sga/get_danger_indication
    path('danger/(?P<organilabcontext>\w+)', views.get_danger_indication, name='get_danger_indication'),
    # sga/get_get_templateList
    url(r'add_personal/(?P<organilabcontext>\w+)', views.create_personal_template, name='add_personal'),
    url(r'edit_personal/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.edit_personal_template, name='edit_personal'),

    url(r'getData/(?P<organilabcontext>\w+)', views.delete_personal, name='getData'),
    url(r'add_substance/(?P<organilabcontext>\w+)', views.create_substance, name='add_substance'),
    url(r'add_recipient_size', views.create_recipient, name='add_recipient_size'),

]