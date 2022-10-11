from django.urls import path

from .views import index_tutorial

urlpatterns = [
    path('tutorial', index_tutorial, name='tutorials')
]