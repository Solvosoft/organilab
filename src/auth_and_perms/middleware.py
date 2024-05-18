from django.conf import settings
from django.contrib.auth import logout as auth_logout, get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.functional import SimpleLazyObject

from auth_and_perms.models import RegistrationUser, ImpostorLog
from django.utils.deprecation import MiddlewareMixin

from auth_and_perms.utils import get_ip_address


class ProfileLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or not user.is_active:
            return
        if not hasattr(user, 'profile'):
            reguser = RegistrationUser.objects.filter(user=user).first()
            if reguser:
                auth_logout(request)
                if reguser.registration_method == 1:
                    return redirect(reverse('auth_and_perms:user_org_creation_totp', args=[user.pk]))
                if reguser.registration_method == 2:
                    return redirect(reverse('auth_and_perms:create_profile_by_digital_signature', args=[user.pk]))
            raise Http404("User has not profile")

        profile = user.profile
        default_profile_lang=profile.language
        languages=list(dict(settings.LANGUAGES).keys())
        if default_profile_lang in  languages:
            translation.activate(default_profile_lang)


class ImpostorMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The Django authentication middleware requires session "
                "middleware to be installed. Edit your MIDDLEWARE setting to "
                "insert "
                "'django.contrib.sessions.middleware.SessionMiddleware' before "
                "'django.contrib.auth.middleware.AuthenticationMiddleware'."
            )
        impostor=request.session.get('impostor', None)
        if impostor:
            User = get_user_model()
            impostor_token = request.COOKIES.get('impostor_token') or None
            ipaddress=get_ip_address(request)
            imposted_as = User.objects.filter(pk=impostor).first()
            if imposted_as and impostor_token:
                impostor_log=ImpostorLog.objects.filter(
                    impostor=request.user,
                    imposted_as=imposted_as,
                    impostor_ip=ipaddress,
                    token=impostor_token
                ).first()
                if impostor_log:
                    request.impostor_info=impostor_log
                    request.user = SimpleLazyObject(lambda: imposted_as)
