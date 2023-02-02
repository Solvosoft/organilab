from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from auth_and_perms.models import ProfilePermission
from django.shortcuts import redirect
from django.urls import reverse

"""
view_shelf
view_shelfobjects
view_shelfobject
view_laboratoryroom
view_laboratory
view_furniture

"""

class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def get_group_permissions(self, user_obj):
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects.filter(**{user_groups_query: user_obj}).values_list('content_type__app_label', 'codename').order_by()

    def process_view(self, request, view_func, view_args, view_kwargs):
        profile_in = None
        user = request.user
        lab_pk=None
        if not user.is_authenticated or not user.is_active:
            return
        if user.is_superuser:
            return

        if hasattr(user, 'profile'):
            profile = user.profile
        else:
            raise Http404("User has not profile")

        if 'lab_pk' in view_kwargs and view_kwargs['lab_pk']:
            lab_pk = view_kwargs['lab_pk']
        elif 'lab_pk' in request.GET and request.GET['lab_pk']:
            lab_pk = request.GET['lab_pk']
        elif 'lab_pk' in request.POST and request.POST['lab_pk']:
            lab_pk = request.POST['lab_pk']
        elif 'lab' in request.GET and request.GET['lab']:
            lab_pk = request.POST['lab']
        elif hasattr(view_func, 'view_class') and hasattr(view_func.view_class, 'lab_pk_field') and \
                view_func.view_class.lab_pk_field in view_kwargs and view_kwargs[view_func.view_class.lab_pk_field
                ] is not None:
            lab_pk = view_kwargs[view_func.view_class.lab_pk_field]
        elif hasattr(view_func, 'lab_pk_field') and view_func.lab_pk_field in view_kwargs and \
                view_kwargs[view_func.lab_pk_field] is not None:
            lab_pk = view_kwargs[view_func.lab_pk_field]

        if lab_pk:
            profile_in = ProfilePermission.objects.filter(profile=user.profile,
                                                          content_type= ContentType.objects.get(app_label='laboratory',
                                                                                                model="laboratory"),
                                                          object_id=lab_pk).first()
        else:
            profile_in = ProfilePermission.objects.filter(profile=profile, object_id=profile.pk,
                                                         content_type=ContentType.objects.filter(
                                                         app_label=profile._meta.app_label,
                                                          model=profile._meta.model_name).first()).first()

        if profile_in:
            roles = profile_in.rol.all()
            user_permissions = []
            for rol in roles:
                user_permissions += list(rol.permissions.values_list('content_type__app_label', 'codename').order_by())

            user_permissions += list(
                request.user.user_permissions.values_list('content_type__app_label', 'codename').order_by())
            user_permissions += list(self.get_group_permissions(request.user))

            if user_permissions:
                request.user._perm_cache = {"%s.%s" % (ct, name) for ct, name in user_permissions}
