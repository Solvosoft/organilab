"""organilab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from laboratory import views
from laboratory.views import LaboratoryRoomListView, FurnitureListView,\
    ObjectListView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    
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
        name="report_summaryfurniture"),
]
