from django import forms
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets

from presentation.models import AlertRule


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


class AlertRuleForm(GTForm, forms.ModelForm):
    """Qué vigilar (proceso y disparador), cuándo (umbral) y a quién avisar.

    Los campos de umbral salen de los disparadores registrados en
    ``djgentelella.alerts``; la plantilla muestra solo los del disparador elegido.
    """

    process = forms.ChoiceField(label=_("Process"), widget=genwidgets.Select)
    trigger = forms.ChoiceField(label=_("Trigger"), widget=genwidgets.Select)
    notification_code = forms.ChoiceField(required=False, label=_("Email"), widget=genwidgets.Select)

    def __init__(self, *args, user=None, **kwargs):
        from djgentelella.async_notification.registry import get_all_contexts

        from presentation.alerts import processes_for, threshold_fields, trigger_choices

        super().__init__(*args, **kwargs)
        processes = processes_for(user) if user is not None else {}
        self.fields["process"].choices = [(code, process.label) for code, process in processes.items()]
        used = {code for process in processes.values() for code in process.triggers}
        self.fields["trigger"].choices = trigger_choices(used)
        self.fields["notification_code"].choices = [("", _("Default of the process"))] + [
            (code, code) for code in sorted(get_all_contexts())
        ]
        for name, (_trigger, field) in threshold_fields().items():
            self.fields[name] = forms.DecimalField(
                required=False, label=field.label, widget=genwidgets.NumberInput
            )
        self.order_fields(["name", "process", "trigger", *threshold_fields()])

    class Meta:
        model = AlertRule
        fields = [
            "name", "process", "trigger", "level", "notification_code", "notify_roles",
            "notify_responsible", "create_task", "is_active",
        ]
        widgets = {
            "name": genwidgets.TextInput,
            "level": genwidgets.Select,
            "notify_roles": genwidgets.SelectMultiple,
            "notify_responsible": genwidgets.YesNoInput,
            "create_task": genwidgets.YesNoInput,
            "is_active": genwidgets.YesNoInput,
        }
