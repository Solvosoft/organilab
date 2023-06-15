"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
"""

# Import functions of another modules
from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import editor
from .views import sustance
from .api.substance_viewset import SubstanceViewSet

router = DefaultRouter()
router.register('api_substance', SubstanceViewSet, basename='api-substance')
# SGA
app_name = 'sga'

# Views
urlpatterns = [

    path('api/', include(router.urls)),
    # sga/index_sga/
    path('editor_sga', editor.render_editor_sga, name='index_editor'),
    path('barcode/<str:code>/', editor.get_barcode_from_number, name='barcode_from_number'),
    # sga/editor
    path('template_editor', editor.template_editor, name='editor'),

    # FIXME: It's necessary this preview ?
    path('get_preview/<int:pk>', editor.get_preview, name='get_preview'),

    # my templates
    path('sustance/create/', sustance.create_edit_sustance, name='create_sustance'),
    path('update_substance/<int:pk>/', sustance.create_edit_sustance, name='update_substance'),
    path('delete_substance/<int:pk>/', sustance.delete_substance, name='delete_substance'),
    path('detail_substance/<int:pk>/', sustance.detail_substance, name='detail_substance'),


    # sga/get_get_templateList
    path('add_personal/', editor.create_personal_template, name='add_personal'),
    path('edit_personal/<int:pk>', editor.edit_personal_template, name='edit_personal'),

    path('delete_sgalabel/<int:pk>', editor.delete_sgalabel, name='delete_sgalabel'),
    path('add_substance', editor.create_substance, name='add_substance'),
    path('add_recipient_size/', editor.create_recipient, name='add_recipient_size'),
    path('company/list/', editor.get_companies, name='get_companies'),
    path('company/add/', editor.create_company, name='add_company'),
    path('company/edit/<int:pk>/', editor.edit_company, name='edit_company'),
    path('company/remove/<int:pk>/', editor.remove_company, name='remove_company'),


    path('sgalabel/get_company/<int:pk>', editor.get_company, name='get_company'),
    path('sgalabel/get_recipient_size/<int:pk>', editor.get_recipient_size, name='get_recipient_size'),
    path('sgalabel/get_sgacomplement_by_substance/<int:pk>', editor.get_sgacomplement_by_substance, name='get_sgacomplement_by_substance'),
    path('sgalabel/create/', editor.create_sgalabel, name='sgalabel_create'),
    path('sgalabel/step_one/<int:pk>', editor.sgalabel_step_one, name='sgalabel_step_one'),
    path('sgalabel/step_two/<int:pk>', editor.sgalabel_step_two, name='sgalabel_step_two'),


    path('get_substance/', sustance.get_substances, name='get_substance'),
    path('approved_substance/', sustance.get_list_substances, name='approved_substance'),
    path('accept_substance/<int:pk>/', sustance.approve_substances, name='accept_substance'),

    path('substance/step_one/<int:pk>/', sustance.create_edit_sustance, name='step_one'),
    path('substance/step_two/<int:pk>/', sustance.step_two, name='step_two'),
    path('substance/step_three/<int:template>/<int:substance>/', sustance.step_three, name='step_three'),
    path('substance/step_four/<int:substance>/', sustance.step_four, name='step_four'),
    path('substance/get_security_leaf/<int:substance>/', sustance.security_leaf_pdf, name='security_leaf_pdf'),
]