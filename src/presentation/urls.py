from django.urls import path

from .views import index_tutorial

urlpatterns = [
    path('tutorial/<int:org_pk>', index_tutorial, name='tutorials')
]