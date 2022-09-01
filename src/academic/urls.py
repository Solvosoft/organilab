'''
Created on 4 may. 2017

@author: luis
'''
from academic.views import add_steps_wrapper, ProcedureListView,\
    ProcedureCreateView, ProcedureUpdateView,procedureStepDetail,ProcedureStepCreateView,\
    ProcedureStepUpdateView, save_object,remove_object,save_observation,remove_observation,\
    delete_step,get_procedure, delete_procedure, generate_reservation
from academic.substance.views import create_edit_sustance, get_substances, get_list_substances, approve_substances


from django.conf.urls import url




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
    url(r'academic/sustance', create_edit_sustance, name='create_sustance'),
    url(r'academic/get_substance', get_substances, name='get_substance'),
    url(r'academic/approved_substance', get_list_substances, name='approved_substance'),
    url(r'academic/accept_substance/(?P<pk>\d+)$', approve_substances, name='accept_substance'),

]
