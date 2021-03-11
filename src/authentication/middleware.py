from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from laboratory.models import ProfilePermission
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
        if 'lab_pk' in view_kwargs and view_kwargs['lab_pk'] is not None:
            profile_in = ProfilePermission.objects.filter(profile=request.user.profile,
                                                          laboratories_id=view_kwargs['lab_pk']).first()

        elif 'lab_pk' in request.GET and request.GET['lab_pk'] is not None:
            profile_in = ProfilePermission.objects.filter(profile=request.user.profile,
                                                          laboratories_id=request.GET.get('lab_pk')).first()
        elif 'lab_pk' in request.POST and request.POST['lab_pk'] is not None:
            profile_in = ProfilePermission.objects.filter(profile=request.user.profile,
                                                      laboratories_id=request.POST.get('lab_pk')).first()

        elif hasattr(view_func, 'view_class') and hasattr(view_func.view_class, 'lab_pk_field') and \
            view_func.view_class.lab_pk_field in view_kwargs  and  view_kwargs[view_func.view_class.lab_pk_field] is not None:
            profile_in = ProfilePermission.objects.filter(profile=request.user.profile,
                                                          laboratories_id=view_kwargs[view_func.view_class.lab_pk_field]).first()
        elif hasattr(view_func, 'lab_pk_field') and view_func.lab_pk_field in view_kwargs and \
                view_kwargs[view_func.lab_pk_field] is not None:
            profile_in = ProfilePermission.objects.filter(profile=request.user.profile,
                                                          laboratories_id=view_kwargs[view_func.lab_pk_field]).first()
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
