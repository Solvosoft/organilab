'''
Created on 4 may. 2017

@author: luis
'''
from academic.views import add_steps_wrapper, ProcedureListView,\
    ProcedureCreateView, ProcedureUpdateView,procedureStepDetail,ProcedureStepCreateView,\
    ProcedureStepUpdateView, save_object,remove_object,save_observation,remove_observation,\
    delete_step,get_procedure, delete_procedure, generate_reservation
from academic.substance.views import create_edit_sustance, get_substances, get_list_substances, \
    approve_substances, delete_substance, step_two, detail_substance, \
    view_warning_words, view_prudence_advices, view_danger_indications, add_sga_complements, add_observation, \
    update_observation, delete_observation, change_prudence_advice, change_warning_word, change_danger_indication, \
    step_three

from django.conf.urls import url
from django.urls import path




urlpatterns = [
    url(r'add_steps_wrapper/(?P<pk>\d+)/lab/(?P<lab_pk>\d+)$',
        add_steps_wrapper, name='add_steps_wrapper'),
    url(r'save_object/(?P<pk>\d+)/(?P<lab_pk>\d+)$',
        save_object, name='save_object'),
    url(r'academic/procedure_list/(?P<pk>\d+)$', ProcedureListView.as_view(), name='procedure_list'),
    url(r'academic/procedure_create/lab/(?P<lab_pk>\d+)$', ProcedureCreateView.as_view(), name='procedure_create'),
    url(r'procedure_update/(?P<pk>\d+)/lab/(?P<lab_pk>\d+)$', ProcedureUpdateView.as_view(), name='procedure_update'),
    url(r'academic/get_procedure$', get_procedure, name='get_procedure'),
    url(r'academic/delete_procedure$', delete_procedure, name='delete_procedure'),
    url(r'procedure_detail/(?P<pk>\d+)/lab/(?P<lab_pk>\d+)$', procedureStepDetail, name='procedure_detail'),
    url(r'academic/procedure/(?P<pk>\d+)/step$', ProcedureStepCreateView.as_view(), name='procedure_step'),
    url(r'academic/step/(?P<pk>\d+)/lab/(?P<lab_pk>\d+)/update$', ProcedureStepUpdateView.as_view(), name='update_step'),
    url(r'academic/step/delete$', delete_step, name='delete_step'),
    url(r'academic/add_object/(?P<pk>\d+)$', save_object, name='add_object'),
    url(r'academic/remove_object/(?P<pk>\d+)$', remove_object, name='remove_object'),
    url(r'academic/add_observation/(?P<pk>\d+)$', save_observation, name='add_observation'),
    url(r'academic/remove_observation/(?P<pk>\d+)$', remove_observation, name='remove_observation'),
    url(r'academic/generate_reservation', generate_reservation, name='generate_reservation'),
    url(r'academic/sustance/(?P<organilabcontext>\w+)', create_edit_sustance, name='create_sustance'),
    url(r'academic/update_substance/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', create_edit_sustance, name='update_substance'),
    url(r'academic/get_substance/(?P<organilabcontext>\w+)', get_substances, name='get_substance'),
    url(r'academic/approved_substance/(?P<organilabcontext>\w+)', get_list_substances, name='approved_substance'),
    url(r'academic/accept_substance/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', approve_substances, name='accept_substance'),
    url(r'academic/delete_substance/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', delete_substance, name='delete_substance'),
    url(r'academic/detail_substance/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', detail_substance, name='detail_substance'),
    url(r'academic/substance/step_one/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', create_edit_sustance, name='step_one'),
    url(r'academic/substance/step_three/(?P<organilabcontext>\w+)/(?P<pk>\d+)$', step_two, name='step_two'),
    url(r'academic/substance/step_two/(?P<organilabcontext>\w+)/(?P<template>\d+)/(?P<substance>\d+)$', step_three, name='step_three'),
    url(r'academic/substance/danger_indications$', view_danger_indications, name='danger_indications'),
    url(r'academic/substance/warning_words$', view_warning_words, name='warning_words'),
    url(r'academic/substance/prudence_advices$', view_prudence_advices, name='prudence_advices'),
    url(r'academic/substance/add_danger_indication$', add_sga_complements, kwargs={'element':'danger'}, name='add_danger_indication'),
    url(r'academic/substance/add_warning_words/', add_sga_complements, kwargs={'element':'warning'}, name='add_warning_word'),
    url(r'academic/substance/add_prudence_advice$', add_sga_complements, kwargs={'element':'prudence'}, name='add_prudence_advice'),
    url(r'academic/substance/add_observation/(?P<organilabcontext>\w+)/(?P<substance>\d+)$', add_observation, name='add_observation'),
    url(r'academic/substance/update_observation$', update_observation, name='update_observation'),
    url(r'academic/substance/deleta_observation$', delete_observation, name='delete_observation'),
    path(r'academic/substance/update_danger_indication/<str:pk>', change_danger_indication, name='update_danger_indication'),
    url(r'academic/substance/update_warning_words/(?P<pk>\d+)$', change_warning_word, name='update_warning_word'),
    url(r'academic/substance/update_prudence_advice/(?P<pk>\d+)$', change_prudence_advice,name='update_prudence_advice'),
]
