from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets


class SystemParameterForm(GTForm, forms.Form):
    value = forms.CharField(
        required=False,
        label=_("Value"),
        help_text=_("Yes/No values: true or false. Dates: YYYY-MM-DD."),
        widget=genwidgets.TextInput,
    )


class NotificationSettingForm(GTForm, forms.Form):
    is_active = forms.BooleanField(required=False, label=_("Send this email"), widget=genwidgets.YesNoInput)
    override_subject = forms.CharField(
        required=False, label=_("Subject"),
        help_text=_("Leave empty to use the subject of the global template."),
        widget=genwidgets.TextInput,
    )
    override_message = forms.CharField(
        required=False, label=_("Message"),
        help_text=_("Leave empty to use the message of the global template. Django template syntax."),
        widget=genwidgets.Textarea(attrs={"rows": 8}),
    )
