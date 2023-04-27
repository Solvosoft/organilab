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
    path('api/informView/', SerializedViews.InformView.as_view(), name='api_inform'),
    path('api/laboratoryView/', SerializedViews.LaboratoryByUserView.as_view(), name='api_laboratory_by_user'),
    path('api/laboratoryOrgView/', SerializedViews.LaboratoryByOrgView.as_view(), name='api_laboratory_by_org'),
    path('api/orgView/', SerializedViews.OrganizationUsersView.as_view(), name='api_org_structure'),
    path('api/incidentReportView/', SerializedViews.IncidentReportView.as_view(), name='api_incident'),
    path('api/objectsView/', SerializedViews.ObjectsView.as_view(), name='api_objects'),
]
