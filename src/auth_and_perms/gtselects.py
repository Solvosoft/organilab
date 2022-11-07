from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics

from auth_and_perms.models import Rol, ProfilePermission
from auth_and_perms.utils import get_roles_by_user


def str2bool(v):
    v = v or ''
    return v.lower() in ("yes", "true", "t", "1")


class GPaginatorMoreElements(GPaginator):
    page_size = 20

@register_lookups(prefix="rolbase", basename="rolbase")
class RolS2OrgManagement(generics.RetrieveAPIView, BaseSelect2View):
    model = Rol
    fields = ['name']
    organization = None
    pagination_class = GPaginatorMoreElements

    def retrieve(self, request, pk, **kwargs):
        self.organization = pk
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if not args:
            raise
        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(organizationstructure=self.organization)
        as_role = str2bool(self.request.GET.get('as_role'))
        if as_role:
            profilepermission = ProfilePermission.objects.filter(
                content_type__app_label=self.request.GET.get('contenttypeobj[appname]'),
                content_type__model=self.request.GET.get('contenttypeobj[model]'),
                object_id=self.request.GET.get('contenttypeobj[objectid]'),
                profile_id=self.request.GET.get('profile')
            ).first()
            if profilepermission:
                self.selected = [str(idpp) for idpp in profilepermission.rol.all().values_list('id', flat=True)]
        return queryset


@register_lookups(prefix="groupbase", basename="groupbase")
class GroupS2(BaseSelect2View):
    model = Rol
    fields = ['name']

    def get_queryset(self):
        user = self.request.user
        return get_roles_by_user(user)