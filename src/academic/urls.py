'''
Created on 4 may. 2017

@author: luis
'''
from django.urls import path

from academic.substance.views import create_edit_sustance, get_substances, get_list_substances, \
    approve_substances, delete_substance, step_two, detail_substance, \
    view_warning_words, view_prudence_advices, view_danger_indications, add_sga_complements, add_observation, \
    update_observation, delete_observation, change_prudence_advice, change_warning_word, change_danger_indication, \
    step_three, step_four, add_sga_provider, security_leaf_pdf
from academic.views import add_steps_wrapper, ProcedureListView, \
    ProcedureCreateView, ProcedureUpdateView, procedureStepDetail, ProcedureStepCreateView, \
    ProcedureStepUpdateView, save_object, remove_object, save_observation, remove_observation, \
    delete_step, get_procedure, delete_procedure, generate_reservation

urlpatterns = [
    path('add_steps_wrapper/<int:pk>/lab/<int:lab_pk>/', add_steps_wrapper, name='add_steps_wrapper'),
    path('save_object/<int:pk>/<int:lab_pk>/', save_object, name='save_object'),
    path('academic/procedure_list/<int:pk>/', ProcedureListView.as_view(), name='procedure_list'),
    path('academic/procedure_create/lab/<int:lab_pk>/', ProcedureCreateView.as_view(), name='procedure_create'),
    path('procedure_update/<int:pk>/lab/<int:lab_pk>/', ProcedureUpdateView.as_view(), name='procedure_update'),
    path('academic/get_procedure/', get_procedure, name='get_procedure'),
    path('academic/delete_procedure/', delete_procedure, name='delete_procedure'),
    path('procedure_detail/<int:pk>/<int:lab_pk>/', procedureStepDetail, name='procedure_detail'),
    path('academic/procedure/<int:pk>/step/', ProcedureStepCreateView.as_view(), name='procedure_step'),
    path('academic/step/<int:pk>/lab/<int:lab_pk>/update/', ProcedureStepUpdateView.as_view(), name='update_step'),
    path('academic/step/delete/', delete_step, name='delete_step'),
    path('academic/add_object/<int:pk>/', save_object, name='add_object'),
    path('academic/remove_object/<int:pk>/', remove_object, name='remove_object'),
    path('academic/add_observation/<int:pk>/', save_observation, name='add_observation'),
    path('academic/remove_observation/<int:pk>/', remove_observation, name='remove_observation'),
    path('academic/generate_reservation', generate_reservation, name='generate_reservation'),
    path('academic/sustance/<str:organilabcontext>/<int:pk_org>/', create_edit_sustance, name='create_sustance'),
    path('academic/update_substance/<str:organilabcontext>/<int:pk_org>/<int:pk>/', create_edit_sustance, name='update_substance'),
    path('academic/get_substance/<str:organilabcontext>/<int:pk>/', get_substances, name='get_substance'),
    path('academic/approved_substance/<str:organilabcontext>/<int:pk>/', get_list_substances, name='approved_substance'),
    path('academic/accept_substance/<str:organilabcontext>/<int:pk>/', approve_substances, name='accept_substance'),
    path('academic/delete_substance/<str:organilabcontext>/<int:pk_org>/<int:pk>/', delete_substance, name='delete_substance'),
    path('academic/detail_substance/<str:organilabcontext>/<int:pk>/', detail_substance, name='detail_substance'),
    path('academic/substance/step_one/<str:organilabcontext>/<int:pk_org>/<int:pk>/', create_edit_sustance, name='step_one'),
    path('academic/substance/step_two/<str:organilabcontext>/<int:pk>/', step_two, name='step_two'),
    path('academic/substance/step_three/<str:organilabcontext>/<int:template>/<int:substance>/', step_three,
         name='step_three'),
    path('academic/substance/step_four/<str:organilabcontext>/<int:substance>/', step_four, name='step_four'),
    path('academic/substance/danger_indications/', view_danger_indications, name='danger_indications'),
    path('academic/substance/warning_words/', view_warning_words, name='warning_words'),
    path('academic/substance/prudence_advices/', view_prudence_advices, name='prudence_advices'),
    path('academic/substance/add_danger_indication/', add_sga_complements, kwargs={'element': 'danger'},
         name='add_danger_indication'),
    path('academic/substance/add_warning_words/', add_sga_complements, kwargs={'element': 'warning'},
         name='add_warning_word'),
    path('academic/substance/add_prudence_advice/', add_sga_complements, kwargs={'element': 'prudence'},
         name='add_prudence_advice'),
    path('academic/substance/add_observation/<str:organilabcontext>/<int:substance>/', add_observation,
         name='add_observation'),
    path('academic/substance/update_observation/', update_observation, name='update_observation'),
    path('academic/substance/deleta_observation/', delete_observation, name='delete_observation'),
    path('academic/substance/update_danger_indication/<str:pk>/', change_danger_indication,
         name='update_danger_indication'),
    path('academic/substance/update_warning_words/<int:pk>/', change_warning_word, name='update_warning_word'),
    path('academic/substance/update_prudence_advice/<int:pk>/', change_prudence_advice, name='update_prudence_advice'),
    path('academic/substance/provider/', add_sga_provider, name='add_sga_provider'),
    path('academic/substance/get_security_leaf/<int:substance>/', security_leaf_pdf, name='security_leaf_pdf'),

]
