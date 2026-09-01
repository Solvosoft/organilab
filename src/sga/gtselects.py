from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from djgentelella.groute import register_lookups
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from auth_and_perms.models import ProfilePermission
from laboratory.models import Catalog, OrganizationStructure, Laboratory
from sga.models import DangerIndication, PrudenceAdvice


def get_user_organizations_queryset(user):
    """Organizaciones sobre las que el usuario tiene ProfilePermission.

    Fuente única compartida por el lookup del widget y por la validación del
    formulario: si divergieran, el desplegable ofrecería opciones que el `clean`
    rechazaría.
    """
    profile = getattr(user, "profile", None)
    if profile is None:
        return OrganizationStructure.objects.none()

    allowed = ProfilePermission.objects.filter(
        profile=profile,
        content_type__app_label="laboratory",
        content_type__model="organizationstructure",
    ).values_list("object_id", flat=True)
    return OrganizationStructure.objects.filter(pk__in=allowed).distinct()


def get_user_laboratories_queryset(user, org_pk):
    """Laboratorios de `org_pk` sobre los que el usuario tiene ProfilePermission."""
    profile = getattr(user, "profile", None)
    if profile is None or not org_pk:
        return Laboratory.objects.none()

    allowed = ProfilePermission.objects.filter(
        profile=profile,
        organization__pk=org_pk,
        content_type__app_label="laboratory",
        content_type__model="laboratory",
    ).values_list("object_id", flat=True)
    return Laboratory.objects.filter(pk__in=allowed).distinct()


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
        allowed = get_user_organizations_queryset(self.request.user)
        return super().get_queryset().filter(pk__in=allowed)


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
        allowed = get_user_laboratories_queryset(self.request.user, self.org)
        return super().get_queryset().filter(pk__in=allowed)

    def list(self, request, *args, **kwargs):
        self.org = self.request.GET.get("org_pk", None)
        return super().list(request, *args, **kwargs)
