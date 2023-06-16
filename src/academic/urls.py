'''
Created on 4 may. 2017

@author: luis
'''
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from academic.api.views import MyProceduresAPI, ProcedureAPI
from academic.views import add_steps_wrapper, ProcedureListView, \
    ProcedureCreateView, ProcedureUpdateView, procedureStepDetail, \
    ProcedureStepCreateView, \
    ProcedureStepUpdateView, save_object, remove_object, save_observation, \
    remove_observation, \
    delete_step, get_procedure, get_my_procedures, delete_procedure, \
    generate_reservation, create_my_procedures, \
    remove_my_procedure, complete_my_procedure


myprocedure = DefaultRouter()
myprocedure.register('api_my_procedure', MyProceduresAPI, basename='api-my-procedure')
myprocedure.register('api_procedures', ProcedureAPI, basename='api-procedure')

procedure_url =[
    path('add_steps_wrapper/<int:pk>/', add_steps_wrapper, name='add_steps_wrapper'),
    re_path('save_object/(?P<pk>\d+)/', save_object, name='save_object'),
    re_path('procedure_list/', ProcedureListView.as_view(), name='procedure_list'),
    re_path('procedure_create/', ProcedureCreateView.as_view(),
            name='procedure_create'),
    re_path('procedure_update/(?P<pk>\d+)/', ProcedureUpdateView.as_view(),
            name='procedure_update'),
    re_path('get_procedure/', get_procedure, name='get_procedure'),
    re_path('delete_procedure/', delete_procedure, name='delete_procedure'),
    re_path('procedure_detail/(?P<pk>\d+)/', procedureStepDetail,
            name='procedure_detail'),
    re_path('procedure/(?P<pk>\d+)/step/', ProcedureStepCreateView.as_view(),
            name='procedure_step'),
    re_path('step/(?P<pk>\d+)/update/', ProcedureStepUpdateView.as_view(),
            name='update_step'),
    re_path('step/delete/', delete_step, name='delete_step'),
    re_path('add_object/(?P<pk>\d+)/', save_object, name='add_object'),
    re_path('remove_object/(?P<pk>\d+)/', remove_object, name='remove_object'),
    re_path('add_observation/(?P<pk>\d+)/', save_observation, name='add_observation'),
    re_path('remove_observation/(?P<pk>\d+)/', remove_observation,
            name='remove_observation'),
    re_path('generate_reservation', generate_reservation, name='generate_reservation'),
    re_path('get_list/', get_my_procedures, name='get_my_procedures'),
    re_path('add_procedures/(?P<content_type>[^/]+)/(?P<model>[^/]+)/',
            create_my_procedures, name='add_my_procedures'),
    re_path('remove_procedure/(?P<pk>[0-9]+)/', remove_my_procedure,
            name='remove_my_procedure'),
    re_path('complete_procedure/(?P<pk>[0-9]+)/', complete_my_procedure,
            name="complete_my_procedure"),
]

urlpatterns = [
    path('<int:lab_pk>/procedure/', include(procedure_url)),
    path('spc/api/<int:lab_pk>/myprocedure/', include(myprocedure.urls)),
]

