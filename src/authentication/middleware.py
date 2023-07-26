from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.http import Http404

from auth_and_perms.models import ProfilePermission
from laboratory.models import OrganizationStructure
from laboratory.utils import get_laboratories_by_user_profile


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
        user = request.user
        lab_pk=None
        org_pk=None
        if not user.is_authenticated or not user.is_active:
            return
        if user.is_superuser:
            return

        if not hasattr(user, 'profile'):
            raise Http404("User has not profile")

        profile = user.profile
        if 'org_pk' in view_kwargs and view_kwargs['org_pk']:
            org_pk = view_kwargs['org_pk']
        if 'lab_pk' in view_kwargs and view_kwargs['lab_pk']:
            lab_pk = view_kwargs['lab_pk']

        if hasattr(view_func, 'view_class') and hasattr(view_func.view_class, 'lab_pk_field') and \
                view_func.view_class.lab_pk_field in view_kwargs and view_kwargs[view_func.view_class.lab_pk_field
                ] is not None:
            lab_pk = view_kwargs[view_func.view_class.lab_pk_field]
        elif hasattr(view_func, 'lab_pk_field') and view_func.lab_pk_field in view_kwargs and \
                view_kwargs[view_func.lab_pk_field] is not None:
            lab_pk = view_kwargs[view_func.lab_pk_field]

        queryQ=Q(profile=profile, object_id=profile.pk,
                 content_type__app_label=profile._meta.app_label,
                 content_type__model=profile._meta.model_name)

        if lab_pk:
            queryQ |= Q(profile=user.profile,object_id=lab_pk,
                        content_type__app_label='laboratory',  content_type__model="laboratory")
        elif org_pk:
            if OrganizationStructure.objects.filter(pk=org_pk, active=False).exists():
                raise Http404("Organization is inactive")
            # for my_labs selection and other steps without laboratory defined
            laboratories = get_laboratories_by_user_profile(request.user, org_pk)
            queryQ |= Q(profile=user.profile,object_id__in=laboratories,
                        content_type__app_label='laboratory',  content_type__model="laboratory")
        if org_pk:
            queryQ |= Q(profile=user.profile, object_id=org_pk,
                        content_type__app_label='laboratory', content_type__model="organizationstructure")

        profile_in = ProfilePermission.objects.filter(queryQ)

        perms = list(profile_in.values_list('rol__permissions__content_type__app_label', 'rol__permissions__codename'))
        user_perms = list(request.user.user_permissions.values_list('content_type__app_label', 'codename'))
        group_permissions = list(self.get_group_permissions(request.user))

        user_permissions = perms+user_perms+group_permissions
        if user_permissions:
            request.user._perm_cache = {"%s.%s" % (ct, name) for ct, name in user_permissions}
