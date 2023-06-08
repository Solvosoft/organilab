"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
"""

# Import functions of another modules
from django.urls import path, re_path

from . import views
from .views import index_sga, template, editor, render_editor_sga

# SGA
app_name = 'sga'

# Views
urlpatterns = [
    # sga/index_sga/
    path('index_sga', index_sga, name='index_sga'),
    path('editor_sga', render_editor_sga, name='index_editor'),
    path('barcode/<str:code>/', views.get_barcode_from_number, name='barcode_from_number'),
    path('label_editor_builder/<str:organilabcontext>/', template, name='template'),
    # sga/editor
    re_path(r'editor/(?P<organilabcontext>\w+)$', editor, name='editor'),
    re_path(r'get_preview/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.get_preview, name='get_preview'),
    re_path(r'get_svgexport/(?P<is_pdf>\d+)/(?P<pk>\d+)$', views.get_svgexport, name='get_svgexport'),

    # sga/prudence
    path('prudence/<str:organilabcontext>', views.get_prudence_advice, name='prudence'),
    # sga/get_danger_indication
    path('danger/<str:organilabcontext>', views.get_danger_indication, name='get_danger_indication'),
    # sga/get_get_templateList
    re_path(r'add_personal/(?P<organilabcontext>\w+)$', views.create_personal_template, name='add_personal'),
    re_path(r'edit_personal/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.edit_personal_template, name='edit_personal'),

    re_path(r'delete_sgalabel/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', views.delete_sgalabel, name='delete_sgalabel'),
    re_path(r'add_substance/(?P<organilabcontext>\w+)', views.create_substance, name='add_substance'),
    path('add_recipient_size/', views.create_recipient, name='add_recipient_size'),
    path('get_pictograms/', views.get_pictograms, name='pictograms_list'),
    path('add_pictogram/', views.add_pictogram, name='add_pictograms'),
    path('update_pictogram/<str:id_pictogram>/', views.update_pictogram, name='update_pictogram'),
    path('company/list/', views.get_companies, name='get_companies'),
    path('company/add/', views.create_company, name='add_company'),
    path('company/edit/<int:pk>/', views.edit_company, name='edit_company'),
    path('company/remove/<int:pk>/', views.remove_company, name='remove_company'),


    path('sgalabel/get_company/<int:pk>', views.get_company, name='get_company'),
    path('sgalabel/get_recipient_size/<str:organilabcontext>/<int:pk>', views.get_recipient_size, name='get_recipient_size'),
    path('sgalabel/get_sgacomplement_by_substance/<int:pk>', views.get_sgacomplement_by_substance, name='get_sgacomplement_by_substance'),
    path('sgalabel/create/<str:organilabcontext>/', views.create_sgalabel, name='sgalabel_create'),
    path('sgalabel/step_one/<str:organilabcontext>/<int:pk>', views.sgalabel_step_one, name='sgalabel_step_one'),
    path('sgalabel/step_two/<str:organilabcontext>/<int:pk>', views.sgalabel_step_two, name='sgalabel_step_two'),

]