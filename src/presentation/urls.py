from django.urls import path

from . import views
from .check_system import do_checks

root_urls = [path("general_info", views.general_information, name="general_info")]

urlpatterns = [
    path("", views.index_organilab, name="index"),
    path("tutorial/<int:org_pk>", views.index_tutorial, name="tutorials"),
    path("tutorial/api/progress/", views.tutorial_progress_api, name="tutorial_progress_api"),
    path("tutorial/api/toggle/", views.tutorial_toggle_api, name="tutorial_toggle_api"),
    path("tutorial/api/reactivate/", views.tutorial_reactivate_api, name="tutorial_reactivate_api"),
    path("feedback", views.FeedbackView.as_view(), name="feedback"),
    path("check_ok", do_checks, name="check_ok"),
    path("error", views.error_view, name="error_view"),
]
