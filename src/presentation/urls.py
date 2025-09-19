from django.urls import path

from . import views
from .check_system import do_checks

root_urls = [path("general_info", views.general_information, name="general_info")]

urlpatterns = [
    path("", views.index_organilab, name="index"),
    path("tutorial/<int:org_pk>", views.index_tutorial, name="tutorials"),
    path("feedback", views.FeedbackView.as_view(), name="feedback"),
    path("check_ok", do_checks, name="check_ok"),
]
