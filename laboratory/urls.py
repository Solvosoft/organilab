from django.conf.urls import url, include
from django.urls import reverse_lazy
from laboratory.views import index, LaboratoryRoomListView, ObjectListView, FurnitureListView
from laboratory import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^login$', auth_views.login, {'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^logout$', auth_views.logout, {'next_page': reverse_lazy('laboratory:index')}, name='logout')
]

# URLS Adolfo
urlpatterns += [
    url(r"^labs$", LaboratoryRoomListView.as_view(),
        name="laboratoryroom_list"),
    url(r"^objects$", ObjectListView.as_view(),
        name="object_list"),
    url(r"^furniture$", FurnitureListView.as_view(),
        name="furniture_list"),
]

urlpatterns += [
    url(r"^report/building$", views.report_building,
        name="report_building"),
    url(r"^report/objects$", views.report_objects,
        name="report_objects"),
    url(r"^report/furniture$", views.report_furniture,
        name="report_furniture"),
    url(r"^report/summaryfurniture$", views.report_sumfurniture,
        name="report_summaryfurniture")
]