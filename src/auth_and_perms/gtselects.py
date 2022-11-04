from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View

from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure


@register_lookups(prefix="rolbase", basename="rolbase")
class Rol(BaseSelect2View):
    model = Rol
    fields = ['name']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        pk = self.request.GET.get('pk', None)
        if pk:
            org = OrganizationStructure.objects.get(pk=int(pk))
            rol_list = list(org.rol.all().values_list('pk', flat=True))
            queryset = queryset.filter(pk__in=rol_list)
        return queryset