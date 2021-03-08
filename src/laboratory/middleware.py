from .models import ProfilePermission
from django.shortcuts import redirect
from django.urls import reverse


class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self,request, view_func, view_args, view_kwargs):

        if 'lab_pk' in view_kwargs:

            profile_in=ProfilePermission.objects.filter(profile=request.user.profile,
                                                     laboratories_id=view_kwargs['lab_pk']).first()
            if profile_in:

                roles = profile_in.rol.all()
                user_permissions=[]

                for rol in roles:
                  user_permissions+=list(rol.permissions.values_list('content_type__app_label', 'codename').order_by())

                user_permissions+=list(request.user.user_permissions.values_list('content_type__app_label', 'codename').order_by())

                if user_permissions:
                    request.user._perm_cache={"%s.%s" % (ct, name) for ct, name in user_permissions}

                print(request.user._perm_cache)

