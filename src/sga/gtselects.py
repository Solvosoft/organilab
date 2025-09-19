from djgentelella.views.select2autocomplete import BaseSelect2View
from djgentelella.groute import register_lookups
from sga.models import DangerIndication, PrudenceAdvice


@register_lookups(prefix="prudence", basename="prudencesearch")
class PrudenceGModelLookup(BaseSelect2View):
    model = PrudenceAdvice
    fields = ["code", "name"]


@register_lookups(prefix="danger", basename="dangersearch")
class DangerGModelLookup(BaseSelect2View):
    model = DangerIndication
    fields = ["code", "description"]
