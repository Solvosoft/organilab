from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View

from auth_and_perms.models import Rol, ProfilePermission


def str2bool(v):
    v = v or ''
    return v.lower() in ("yes", "true", "t", "1")

@register_lookups(prefix="rolbase", basename="rolbase")
class Rol(BaseSelect2View):
    model = Rol
    fields = ['name']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        org = self.request.GET.get('organization', None)
        if org:
            queryset = queryset.filter(organizationstructure=42)
        as_role = str2bool(self.request.GET.get('context[as_role]'))
        if as_role:
            profilepermission = ProfilePermission.objects.filter(
                content_type__app_label=self.request.GET.get('context[profile][appname]'),
                content_type__model=self.request.GET.get('context[profile][model]'),
                object_id=self.request.GET.get('context[profile][object_id]'),
                profile_id=self.request.GET.get('context[profile][profile]')
            ).first()
            if profilepermission:
                self.selected = list(profilepermission.rol.all().values_list('id', flat=True))
        return queryset