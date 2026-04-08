from django import forms
from django.utils.translation import gettext_lazy as _

from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from pending_tasks.models import PendingTask
from djgentelella.widgets.wysiwyg import TextareaWysiwyg


class PendingTaskForm(GTForm, forms.ModelForm):

    class Meta:
        model = PendingTask
        fields = ["name", "description", "status", "profile", "rols", "link"]
        widgets = {
            "name": genwidgets.TextInput,
            "description": TextareaWysiwyg,  # (attrs={"data-option-lang": "es"}),
            "status": genwidgets.Select,
            "profile": AutocompleteSelect("profiles_ref"),
            # "rols": AutocompleteSelectMultiple("roluserorgbase"),
            "link": genwidgets.URLInput,
        }

    def __init__(self, *args, **kwargs):
        super(PendingTaskForm, self).__init__(*args, **kwargs)
        self.fields["profile"].label = _("User")
