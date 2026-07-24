from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from djgentelella.groute import register_lookups
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from auth_and_perms.models import ProfilePermission
from laboratory.models import Catalog, OrganizationStructure, Laboratory
from sga.models import DangerIndication, PrudenceAdvice


@register_lookups(prefix="prudence", basename="prudencesearch")
class PrudenceGModelLookup(BaseSelect2View):
    model = PrudenceAdvice
    fields = ["code", "name"]


@register_lookups(prefix="danger", basename="dangersearch")
class DangerGModelLookup(BaseSelect2View):
    model = DangerIndication
    fields = ["code", "description"]


@register_lookups(prefix="catalogsga", basename="catalogsga")
class CatalogUnitLookup(BaseSelect2View):
    model = Catalog
    fields = ["description"]
    authentication_classes = [SessionAuthentication]
    perms = {
        "list": ["laboratory.view_catalog"],
    }
    permission_classes = (AnyPermissionByAction,)
    serializer = None
    shelf = None

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(key="units", description__in=["Litros", "Kilogramos", "Libra"])
        )
        return queryset


class GPaginatorMoreElements(GPaginator):
    page_size = 100


@register_lookups(prefix="user_organization_loop", basename="user_organization_loop")
class OrganizationUserLookup(BaseSelect2View):
    model = OrganizationStructure
    fields = ["name"]
    ordering = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        pp_organization = ProfilePermission.objects.filter(
            profile=self.request.user.profile,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        ).values_list("object_id", flat=True)
        queryset = queryset.filter(pk__in=pp_organization).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@register_lookups(prefix="user_laboratory_loop", basename="user_laboratory_loop")
class UserLaboratoryLookup(BaseSelect2View):
    model = Laboratory
    fields = ["name"]
    ordering = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer, org = None, None

    def get_queryset(self):
        queryset = super().get_queryset()
        pp_labs = ProfilePermission.objects.filter(
            profile=self.request.user.profile,
            organization__pk=self.org,
            content_type__app_label="laboratory",
            content_type__model="laboratory",
        ).values_list("object_id", flat=True)
        queryset = queryset.filter(pk__in=pp_labs).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        self.org = self.request.GET.get("org_pk", None)
        return super().list(request, *args, **kwargs)
