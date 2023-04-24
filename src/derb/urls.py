from django.urls import path

import derb.api.views as SerializedViews
from .views import form_list, preview_form
from .views import EditView
from .views.EditView import UpdateForm


app_name = 'derb'

urlpatterns = [
    path('FormList/', form_list.FormList.as_view(), name='form_list'),
    path('FormList/delete/<int:pk>/', form_list.DeleteForm.as_view(), name='delete_form'),
    path('FormList/create/', form_list.CreateForm, name='create_form'),
    path('FormList/preview/<int:form_id>/', preview_form.previewForm, name='preview_form'),
    path('editView/', EditView.as_view(), name='edit_view'),
    path('editView/<int:form_id>/', EditView.as_view(), name='edit_view'),
    path('editView/update/', UpdateForm, name='update_form'),
    path('informView/', SerializedViews.InformView.as_view(), name='inform_view'),
    path('laboratoryView/', SerializedViews.LaboratorytView.as_view(), name='laboratory_view'),
    path('orgView/', SerializedViews.OrganizationUsersView.as_view(), name='org_structure_view'),
    path('incidentReportView/', SerializedViews.IncidentReportView.as_view(), name='incident_view'),
    path('objectsView/', SerializedViews.ObjectsView.as_view(), name='objects_view'),
]
