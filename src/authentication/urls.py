# encoding: utf-8

'''
Created on 20 jun. 2018

@author: luisza
'''

from django.contrib.auth import views as auth_views
from django.conf.urls import url
from django.urls.base import reverse_lazy
from authentication.views import signup, OrgLoginView, PermissionDeniedView,\
    FeedbackView

urlpatterns = [

    url(r'^signup$', signup, name='signup'),
    url(r'^accounts/login/$', OrgLoginView.as_view(),
        {'template_name': 'registration/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.LogoutView, {
        'next_page': reverse_lazy('index')},
        name='logout'),

    url(r'^permission_denied$', PermissionDeniedView.as_view(),
        name='permission_denied'),
    url(r'^feedback$', FeedbackView.as_view(), name='feedback'),

    # Password_reset
    url(r'^accounts/password_reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_ss.html',
            email_template_name='registration/password_reset_email_ss.html',
            subject_template_name='registration/password_reset_subject_ss.txt',
            success_url='/accounts/password_reset_done/'),
        name='password_reset'),  # Set a sending e-mail on 'from_email'.
    url(r'^accounts/password_reset_done/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done_ss.html'),
        name='password_reset_done'),
    url(r'^accounts/password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm_ss.html',
            success_url='/accounts/password_reset_complete/'),
        name='password_reset_confirm'),
    url(r'^accounts/password_reset_complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete_ss.html'),
        name='password_reset_complete'),


]
