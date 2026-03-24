from django import forms
from django.utils.translation import gettext_lazy as _

from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from pending_tasks.models import PendingTask


class PendingTaskForm(GTForm, forms.ModelForm):
    organization = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = PendingTask
        fields = ["name", "description", "status", "profile", "rols", "link"]
        widgets = {
            "name": genwidgets.TextInput,
            "description": genwidgets.Textarea,
            "status": genwidgets.Select,
            "profile": AutocompleteSelect("org_profiles"),
            "rols": AutocompleteSelectMultiple("roluserorgbase"),
            "link": genwidgets.URLInput,
        }

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop("org_pk", None)
        super(PendingTaskForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields["organization"].initial = org_pk
            prefix = self.prefix
            org_field_id = (
                f"#id_{prefix}-organization" if prefix else "#id_organization"
            )
            self.fields["profile"].widget.attrs.update(
                {"data-s2filter-organization": org_field_id}
            )
