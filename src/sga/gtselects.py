from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View
from sga.models import DangerIndication

@register_lookups(prefix="danger", basename="dangerbasename")
class DangerModelLookup(BaseSelect2View):
    model = DangerIndication
    fields = ['code']