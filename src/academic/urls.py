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


procedure = DefaultRouter()
myprocedure = DefaultRouter()
myprocedure.register('api_my_procedure', MyProceduresAPI, basename='api-my-procedure')
procedure.register('api_procedures', ProcedureAPI, basename='api-procedure')

procedure_url =[
    path('add_steps_wrapper/<int:pk>/', add_steps_wrapper, name='add_steps_wrapper'),
    path('save_object/<int:pk>/', save_object, name='save_object'),
    path('procedure_create/', ProcedureCreateView.as_view(),
            name='procedure_create'),
    path('procedure_update/<int:pk>/', ProcedureUpdateView.as_view(),
            name='procedure_update'),
    path('get_procedure/<int:pk>/', get_procedure, name='get_procedure'),
    path('delete_procedure/', delete_procedure, name='delete_procedure'),
    path('procedure_detail/<int:pk>/', procedureStepDetail,
            name='procedure_detail'),
    path('procedure/<int:pk>/step/', ProcedureStepCreateView.as_view(),
            name='procedure_step'),
    path('step/<int:pk>/update/', ProcedureStepUpdateView.as_view(),
            name='update_step'),
    path('step/delete/', delete_step, name='delete_step'),
    path('add_object/(<int:pk>/', save_object, name='add_object'),
    path('remove_object/<int:pk>/', remove_object, name='remove_object'),
    path('add_observation/<int:pk>/', save_observation, name='add_observation'),
    path('remove_observation/<int:pk>/', remove_observation,
            name='remove_observation'),
    path('procedure_list/', ProcedureListView.as_view(), name='procedure_list'),
]

my_procedure_url = [
    path('generate_reservation/', generate_reservation, name='generate_reservation'),
    path('get_list/', get_my_procedures, name='get_my_procedures'),
    path('add_procedures/<str:content_type>/<str:model>/', create_my_procedures,
         name='add_my_procedures'),
    path('remove_procedure/<int:pk>/', remove_my_procedure,
         name='remove_my_procedure'),
    path('complete_procedure/<int:pk>/', complete_my_procedure,
         name="complete_my_procedure"),
]

urlpatterns = [
    path('procedure/', include(procedure_url)),
    path('myprocedure/<int:lab_pk>/', include(my_procedure_url)),
    path('spc/api/myprocedure/<int:lab_pk>/', include(myprocedure.urls)),
    path('spc/api/procedure/', include(procedure.urls)),


]

