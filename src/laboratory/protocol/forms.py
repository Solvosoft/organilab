from djgentelella.forms.forms import GTForm
from djgentelella.widgets.files import FileChunkedUpload

from laboratory import forms
from laboratory.models import Protocol
from djgentelella.widgets import core as genwidgets


class ProtocolForm(forms.ModelForm, GTForm):
    class Meta:
        model = Protocol
        fields = ["name", "short_description", "file"]
        widgets = {
            "name": genwidgets.TextInput,
            "short_description": genwidgets.Textarea,
            "file": FileChunkedUpload,
        }
