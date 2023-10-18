from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.http import Http404

from auth_and_perms.models import ProfilePermission
from laboratory.models import OrganizationStructure
from laboratory.utils import get_laboratories_by_user_profile
from django.utils import translation

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
            raise Http404("User has not profile")

        profile = user.profile
        default_profile_lang=profile.language
        languages=list(dict(settings.LANGUAGES).keys())
        if default_profile_lang in  languages:
            translation.activate(default_profile_lang)

