from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups
from rest_framework.authentication import SessionAuthentication

from laboratory.models import Catalog
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
        queryset = super().get_queryset().filter(key="units",
                                                 description__in=["Litros","Kilogramos",
                                                                  "Libra"])
        return queryset
