'''
Created on 4 may. 2017

@author: luis
'''
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from academic.api.views import ReviewSubstanceViewSet
from academic.substance.views import create_edit_sustance, get_substances, get_list_substances, \
    approve_substances, delete_substance, step_two, detail_substance, \
    view_warning_words, view_prudence_advices, view_danger_indications, add_sga_complements, add_observation, \
    update_observation, delete_observation, change_prudence_advice, change_warning_word, change_danger_indication, \
    step_three, step_four, add_sga_provider, security_leaf_pdf
from academic.views import add_steps_wrapper, ProcedureListView, \
    ProcedureCreateView, ProcedureUpdateView, procedureStepDetail, ProcedureStepCreateView, \
    ProcedureStepUpdateView, save_object, remove_object, save_observation, remove_observation, \
    delete_step, get_procedure, delete_procedure, generate_reservation


"""APIS"""
router = DefaultRouter()

router.register('api_reviewsubstance', ReviewSubstanceViewSet, basename='api-reviewsubstance')

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

]
urlpatterns = [
    path('academic/sustance/<str:organilabcontext>/<int:org_pk>/', create_edit_sustance, name='create_sustance'),
    path('academic/update_substance/<str:organilabcontext>/<int:org_pk>/<int:pk>/', create_edit_sustance, name='update_substance'),
    path('academic/get_substance/<str:organilabcontext>/<int:org_pk>/', get_substances, name='get_substance'),
    path('academic/approved_substance/<str:organilabcontext>/<int:org_pk>', get_list_substances, name='approved_substance'),
    path('academic/accept_substance/<str:organilabcontext>/<int:org_pk>/<int:pk>/', approve_substances, name='accept_substance'),
    path('academic/delete_substance/<str:organilabcontext>/<int:org_pk>/<int:pk>/', delete_substance, name='delete_substance'),
    path('academic/detail_substance/<str:organilabcontext>/<int:org_pk>/<int:pk>/', detail_substance, name='detail_substance'),
    path('academic/substance/step_one/<str:organilabcontext>/<int:org_pk>/<int:pk>/', create_edit_sustance, name='step_one'),
    path('academic/substance/step_two/<str:organilabcontext>/<int:org_pk>/<int:pk>/', step_two, name='step_two'),
    path('academic/substance/step_three/<str:organilabcontext>/<int:org_pk>/<int:template>/<int:substance>/', step_three,
         name='step_three'),
    path('academic/substance/step_four/<str:organilabcontext>/<int:org_pk>/<int:substance>/', step_four, name='step_four'),
    path('academic/substance/danger_indications/', view_danger_indications, name='danger_indications'),
    path('academic/substance/warning_words/', view_warning_words, name='warning_words'),
    path('academic/substance/prudence_advices/', view_prudence_advices, name='prudence_advices'),
    path('academic/substance/add_danger_indication/', add_sga_complements, kwargs={'element': 'danger'},
         name='add_danger_indication'),
    path('academic/substance/add_warning_words/', add_sga_complements, kwargs={'element': 'warning'},
         name='add_warning_word'),
    path('academic/substance/add_prudence_advice/', add_sga_complements, kwargs={'element': 'prudence'},
         name='add_prudence_advice'),
    path('academic/substance/add_observation/<str:organilabcontext>/<int:org_pk>/<int:substance>/', add_observation,
         name='add_observation'),
    path('academic/substance/update_observation/', update_observation, name='update_observation'),
    path('academic/substance/deleta_observation/', delete_observation, name='delete_observation'),
    path('academic/substance/update_danger_indication/<str:pk>/', change_danger_indication,
         name='update_danger_indication'),
    path('academic/substance/update_warning_words/<int:pk>/', change_warning_word, name='update_warning_word'),
    path('academic/substance/update_prudence_advice/<int:pk>/', change_prudence_advice, name='update_prudence_advice'),
    path('academic/substance/provider/', add_sga_provider, name='add_sga_provider'),
    path('academic/substance/get_security_leaf/<int:substance>/', security_leaf_pdf, name='security_leaf_pdf'),
    path('academic/api/', include(router.urls)),
    re_path(r'^academic/(?P<lab_pk>\d+)/(?P<org_pk>\d+)/procedure/', include(procedure_url)),

]
