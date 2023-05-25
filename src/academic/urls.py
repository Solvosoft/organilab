'''
Created on 4 may. 2017

@author: luis
'''
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from academic.substance.views import create_edit_sustance, get_substances, get_list_substances, \
    approve_substances, delete_substance, step_two, detail_substance, \
    view_warning_words, view_prudence_advices, view_danger_indications, add_sga_complements, add_observation, \
    update_observation, delete_observation, change_prudence_advice, change_warning_word, change_danger_indication, \
    step_three, step_four, add_sga_provider, security_leaf_pdf
from academic.views import add_steps_wrapper, ProcedureListView, \
    ProcedureCreateView, ProcedureUpdateView, procedureStepDetail, ProcedureStepCreateView, \
    ProcedureStepUpdateView, save_object, remove_object, save_observation, remove_observation, \
    delete_step, get_procedure, get_my_procedures, delete_procedure, generate_reservation, create_my_procedures, \
    remove_my_procedure, complete_my_procedure

procedure_url =[
    re_path('add_steps_wrapper/(?P<pk>\d+)/', add_steps_wrapper, name='add_steps_wrapper'),
    re_path('save_object/(?P<pk>\d+)/', save_object, name='save_object'),
    re_path('procedure_list/', ProcedureListView.as_view(), name='procedure_list'),
    re_path('procedure_create/', ProcedureCreateView.as_view(), name='procedure_create'),
    re_path('procedure_update/(?P<pk>\d+)/', ProcedureUpdateView.as_view(), name='procedure_update'),
    re_path('get_procedure/', get_procedure, name='get_procedure'),
    re_path('delete_procedure/', delete_procedure, name='delete_procedure'),
    re_path('procedure_detail/(?P<pk>\d+)/', procedureStepDetail, name='procedure_detail'),
    re_path('procedure/(?P<pk>\d+)/step/', ProcedureStepCreateView.as_view(), name='procedure_step'),
    re_path('step/(?P<pk>\d+)/update/', ProcedureStepUpdateView.as_view(), name='update_step'),
    re_path('step/delete/', delete_step, name='delete_step'),
    re_path('add_object/(?P<pk>\d+)/', save_object, name='add_object'),
    re_path('remove_object/(?P<pk>\d+)/', remove_object, name='remove_object'),
    re_path('add_observation/(?P<pk>\d+)/', save_observation, name='add_observation'),
    re_path('remove_observation/(?P<pk>\d+)/', remove_observation, name='remove_observation'),
    re_path('generate_reservation', generate_reservation, name='generate_reservation'),
    re_path('get_list/', get_my_procedures, name='get_my_procedures'),
    re_path('add_procedures/(?P<content_type>[^/]+)/(?P<model>[^/]+)/', create_my_procedures, name='add_my_procedures'),
    re_path('remove_procedure/(?P<pk>[0-9]+)/', remove_my_procedure, name='remove_my_procedure'),
    re_path('complete_procedure/(?P<pk>[0-9]+)/', complete_my_procedure, name="complete_my_procedure"),
]

urlpatterns = [
    path('sustance/<str:organilabcontext>/', create_edit_sustance, name='create_sustance'),
    path('update_substance/<str:organilabcontext>/<int:pk>/', create_edit_sustance, name='update_substance'),
    path('get_substance/<str:organilabcontext>/', get_substances, name='get_substance'),
    path('approved_substance/<str:organilabcontext>/', get_list_substances, name='approved_substance'),
    path('accept_substance/<str:organilabcontext>/<int:pk>/', approve_substances, name='accept_substance'),
    path('delete_substance/<str:organilabcontext>/<int:pk>/', delete_substance, name='delete_substance'),
    path('detail_substance/<str:organilabcontext>/<int:pk>/', detail_substance, name='detail_substance'),
    path('substance/step_one/<str:organilabcontext>/<int:pk>/', create_edit_sustance, name='step_one'),
    path('substance/step_two/<str:organilabcontext>/<int:pk>/', step_two, name='step_two'),
    path('substance/step_three/<str:organilabcontext>/<int:template>/<int:substance>/', step_three, name='step_three'),
    path('substance/step_four/<str:organilabcontext>/<int:substance>/', step_four, name='step_four'),
    path('substance/danger_indications/', view_danger_indications, name='danger_indications'),
    path('substance/warning_words/', view_warning_words, name='warning_words'),
    path('substance/prudence_advices/', view_prudence_advices, name='prudence_advices'),
    path('substance/add_danger_indication/', add_sga_complements, kwargs={'element': 'danger'}, name='add_danger_indication'),
    path('substance/add_warning_words/', add_sga_complements, kwargs={'element': 'warning'}, name='add_warning_word'),
    path('substance/add_prudence_advice/', add_sga_complements, kwargs={'element': 'prudence'}, name='add_prudence_advice'),
    path('substance/add_observation/<str:organilabcontext>/<int:substance>/', add_observation, name='add_observation'),
    path('substance/update_observation/', update_observation, name='update_observation'),
    path('substance/deleta_observation/', delete_observation, name='delete_observation'),
    path('substance/update_danger_indication/<str:pk>/', change_danger_indication, name='update_danger_indication'),
    path('substance/update_warning_words/<int:pk>/', change_warning_word, name='update_warning_word'),
    path('substance/update_prudence_advice/<int:pk>/', change_prudence_advice, name='update_prudence_advice'),
    path('substance/provider/', add_sga_provider, name='add_sga_provider'),
    path('substance/get_security_leaf/<int:substance>/', security_leaf_pdf, name='security_leaf_pdf'),
    re_path(r'^(?P<lab_pk>\d+)/procedure/', include(procedure_url)),
]
