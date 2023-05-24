from django.forms import ModelForm
from djgentelella.forms.forms import GTForm
from django import forms
from djgentelella.widgets import core as genwidgets
from django.utils.translation import gettext_lazy as _
from djgentelella.widgets.selects import AutocompleteSelect

from laboratory import utils

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, Provider, Shelf, LaboratoryRoom, Furniture
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

class AddShelfObjectForm(GTForm):
    amount = forms.FloatField(widget=genwidgets.TextInput, help_text='Use dot like 0.344 on decimal',
                              label=_('Amount'), required=True)
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"), required=False)
    provider = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Provider.objects.all(),
                                      label=_("Provider"), required=False)

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        super(AddShelfObjectForm, self).__init__(*args, **kwargs)
        providers = Provider.objects.filter(laboratory__id=int(lab))
        self.fields['provider'].queryset = providers

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

class SubstractShelfObjectForm(GTForm):
    discount = forms.DecimalField(widget=genwidgets.TextInput, help_text='Use dot like 0.344 on decimal',
                                  label=_('Amount'), required=True)
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text='Describe the action',
                                  label=_('Description'), required=False)


class MoveShelfObjectForm(GTForm):
    organization = forms.IntegerField(widget=forms.HiddenInput)
    laboratory = forms.IntegerField(widget=forms.HiddenInput)
    exclude_shelf = forms.IntegerField(widget=forms.HiddenInput)
    lab_room = forms.ModelChoiceField(queryset=LaboratoryRoom.objects.all(), label=_("Laboratory Room"),
                                      widget=AutocompleteSelect("lab_room", attrs={
                                          'data-related': 'true',
                                          'data-pos': 0,
                                          'data-groupname': 'moveshelfform',
                                          'data-s2filter-organization': '#id_organization',
                                          'data-s2filter-laboratory': '#id_laboratory'
                                      })
                                      )
    furniture = forms.ModelChoiceField(queryset=Furniture.objects.all(), label=_("Furniture"),
                                       widget=AutocompleteSelect("furniture", attrs={
                                           'data-related': 'true',
                                           'data-pos': 1,
                                           'data-groupname': 'moveshelfform',
                                           'data-s2filter-organization': '#id_organization',
                                           'data-s2filter-laboratory': '#id_laboratory'
                                       })
                                       )
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.all(), label=_("Shelf"),
                                   widget=AutocompleteSelect("shelf", attrs={
                                       'data-related': 'true',
                                       'data-pos': 2,
                                       'data-groupname': 'moveshelfform',
                                       'data-s2filter-exclude_shelf': '#id_shelf',
                                       'data-s2filter-organization': '#id_organization',
                                       'data-s2filter-laboratory': '#id_laboratory'
                                   })
                                   )

class ExcludeShelfForm(GTForm):
    exclude_shelf = forms.IntegerField()