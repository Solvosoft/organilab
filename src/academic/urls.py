'''
Created on 4 may. 2017

@author: luis
'''
from academic.views import ProcedureView, StepsView, add_steps_wrapper
from django.conf.urls import url, include


procView = ProcedureView().get_urls()
stepView = StepsView().get_urls()


urlpatterns = [
    url(r'add_steps_wrapper/(?P<pk>\d+)$',
        add_steps_wrapper, name='add_steps_wrapper'),

] +procView + stepView
