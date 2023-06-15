"""
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
"""

# Import functions of another modules
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.substance_viewset import SubstanceViewSet
from .views import editor
from .views.substance import views as substance

router = DefaultRouter()
router.register('api_substance', SubstanceViewSet, basename='api-substance')
# SGA
app_name = 'sga'

# Views
urlpatterns = [

    path('api/', include(router.urls)),
    # sga/index_sga/
    path('editor_sga', editor.render_editor_sga, name='index_editor'),
    path('barcode/<str:code>/', editor.get_barcode_from_number,
         name='barcode_from_number'),
    # sga/editor
    path('template_editor', editor.template_editor, name='editor'),

    # FIXME: It's necessary this preview ?
    path('get_preview/<int:pk>', editor.get_preview, name='get_preview'),

    # my templates
    path('sustance/create/', substance.create_edit_sustance, name='create_sustance'),
    path('update_substance/<int:pk>/', substance.create_edit_sustance,
         name='update_substance'),
    path('delete_substance/<int:pk>/', substance.delete_substance,
         name='delete_substance'),
    path('detail_substance/<int:pk>/', substance.detail_substance,
         name='detail_substance'),

    # sga/get_get_templateList
    path('add_personal/', editor.create_personal_template, name='add_personal'),
    path('edit_personal/<int:pk>', editor.edit_personal_template, name='edit_personal'),

    path('delete_sgalabel/<int:pk>', editor.delete_sgalabel, name='delete_sgalabel'),
    path('add_recipient_size/', editor.create_recipient, name='add_recipient_size'),
    path('company/list/', editor.get_companies, name='get_companies'),
    path('company/add/', editor.create_company, name='add_company'),
    path('company/edit/<int:pk>/', editor.edit_company, name='edit_company'),
    path('company/remove/<int:pk>/', editor.remove_company, name='remove_company'),

    path('sgalabel/get_company/<int:pk>', editor.get_company, name='get_company'),
    path('sgalabel/get_recipient_size/<int:pk>', editor.get_recipient_size,
         name='get_recipient_size'),
    path('sgalabel/get_sgacomplement_by_substance/<int:pk>',
         editor.get_sgacomplement_by_substance, name='get_sgacomplement_by_substance'),
    path('sgalabel/create/', editor.create_sgalabel, name='sgalabel_create'),
    path('sgalabel/step_one/<int:pk>', editor.sgalabel_step_one,
         name='sgalabel_step_one'),
    path('sgalabel/step_two/<int:pk>', editor.sgalabel_step_two,
         name='sgalabel_step_two'),

    path('get_substance/', substance.get_substances, name='get_substance'),
    path('approved_substance/', substance.get_list_substances,
         name='approved_substance'),
    path('accept_substance/<int:pk>/', substance.approve_substances,
         name='accept_substance'),

    path('substance/step_one/<int:pk>/', substance.create_edit_sustance,
         name='step_one'),
    path('substance/step_two/<int:pk>/', substance.step_two, name='step_two'),
    path('substance/step_three/<int:template>/<int:substance>/', substance.step_three,
         name='step_three'),
    path('substance/step_four/<int:substance>/', substance.step_four, name='step_four'),
    path('substance/get_security_leaf/<int:substance>/', substance.security_leaf_pdf,
         name='security_leaf_pdf'),
    path('substance/danger_indications/', substance.view_danger_indications,
         name='danger_indications'),
    path('substance/warning_words/', substance.view_warning_words,
         name='warning_words'),
    path('substance/prudence_advices/', substance.view_prudence_advices,
         name='prudence_advices'),
    path('substance/add_danger_indication/', substance.add_sga_complements,
         kwargs={'element': 'danger'},
         name='add_danger_indication'),
    path('substance/add_warning_words/', substance.add_sga_complements,
         kwargs={'element': 'warning'},
         name='add_warning_word'),
    path('substance/add_prudence_advice/', substance.add_sga_complements,
         kwargs={'element': 'prudence'},
         name='add_prudence_advice'),
    path('substance/add_observation/<int:substance>/', substance.add_observation,
         name='add_observation'),
    path('substance/update_observation/', substance.update_observation,
         name='update_observation'),
    path('substance/deleta_observation/', substance.delete_observation,
         name='delete_observation'),
    path('substance/update_danger_indication/<str:pk>/',
         substance.change_danger_indication, name='update_danger_indication'),
    path('substance/update_warning_words/<int:pk>/', substance.change_warning_word,
         name='update_warning_word'),
    path('substance/update_prudence_advice/<int:pk>/', substance.change_prudence_advice,
         name='update_prudence_advice'),
    path('substance/provider/', substance.add_sga_provider, name='add_sga_provider'),
]
