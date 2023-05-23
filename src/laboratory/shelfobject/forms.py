from django.forms import ModelForm
from djgentelella.forms.forms import GTForm
from django import forms
from djgentelella.widgets import core as genwidgets
from django.utils.translation import gettext_lazy as _
from djgentelella.widgets.selects import AutocompleteSelectMultiple

from laboratory import utils

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, Provider
from reservations_management.models import ReservedProducts


class ReserveShelfObjectForm(ModelForm, GTForm):

    class Meta:
        model = ReservedProducts
        fields = ['amount_required', 'initial_date', 'final_date']
        widgets = {
            'initial_date': genwidgets.DateTimeInput,
            'final_date': genwidgets.DateTimeInput,
            'amount_required': genwidgets.TextInput
        }

class IncreaseShelfObjectForm(GTForm):
    amount = forms.FloatField(widget=genwidgets.TextInput, help_text='Use dot like 0.344 on decimal', label=_('Amount'))
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"), required=False)
    provider = forms.ModelChoiceField(queryset=Provider.objects.all(), label=_("Provider"), required=False,
                                      widget=AutocompleteSelectMultiple("provider", attrs={
                                          'data-s2filter-laboratory': '#id_laboratory',
                                      })
                                      )

class TransferOutShelfObjectForm(GTForm):
    amount_to_transfer = forms.FloatField(widget=genwidgets.NumberInput, label=_('Amount'),
                                  help_text=_('Use dot like 0.344 on decimal'), required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.none(),
                                        label=_("Laboratory"), required=True)
    mark_as_discard = forms.BooleanField(widget=genwidgets.YesNoInput, required=False)

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab = kwargs.pop('lab_send')
        org = kwargs.pop('org')
        super(TransferOutShelfObjectForm, self).__init__(*args, **kwargs)
        profile = Profile.objects.filter(pk=users.profile.pk).first()
        orgs = utils.get_pk_org_ancestors_decendants(users, org)

        self.fields['laboratory'].queryset = profile.laboratories.filter(organization__in=orgs).exclude(pk=lab)

class DecreaseShelfObjectForm(GTForm):
    amount = forms.DecimalField(widget=genwidgets.TextInput, help_text='Use dot like 0.344 on decimal', label=_('Amount'))
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text='Describe the action',
                                  label=_('Description'), required=False)


class ValidateLaboratoryForm(GTForm):
    laboratory = forms.IntegerField()