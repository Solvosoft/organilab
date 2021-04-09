from django import forms
from django.contrib.auth.models import Group, User
from djgentelella.forms.forms import CustomForm

from sga.models import DangerIndication
from .models import Laboratory, Object, Profile,Rol,ProfilePermission,Provider,Shelf
from reservations_management.models import ReservedProducts
from django.contrib.auth.forms import UserCreationForm
from djgentelella.widgets.selects import AutocompleteSelectMultipleBase,AutocompleteSelectBase
from django.utils.translation import ugettext_lazy as _
from laboratory.models import OrganizationStructure
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from django.forms import ModelForm


class ObjectSearchForm(CustomForm, forms.Form):
    q = forms.ModelMultipleChoiceField(queryset=Object.objects.all(), widget=genwidgets.SelectMultiple,
                                       required=False, label=_("Search by name, code or CAS number"))

    all_labs = forms.BooleanField(
        widget=genwidgets.YesNoInput, required=False, label=_("All labs"))


class UserCreate(UserCreationForm):
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    email = forms.EmailField(label=_('Email'))

    def save(self):
        user = super(UserCreate, self).save()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        return user


class UserAccessForm(forms.Form):
    access = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'id': 'user_cb_'}))  # User_checkbox_id
    # For delete users. Add a delete button.


class LaboratoryCreate(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(LaboratoryCreate, self).__init__(*args, **kwargs)
        self.fields['organization'].queryset = \
            OrganizationStructure.os_manager.filter_user(user)

    class Meta:
        model = Laboratory
        fields = ['name', 'phone_number', 'location',
                  'geolocation', 'organization']

class LaboratoryEdit(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(LaboratoryEdit, self).__init__(*args, **kwargs)
        self.fields['organization'].queryset = \
            OrganizationStructure.os_manager.filter_user(user)

    class Meta:
        model = Laboratory
        fields = ['name', 'coordinator', 'unit','phone_number', 'email', 'location',
                  'geolocation', 'organization']


class H_CodeForm(forms.Form):
    hcode = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all(), required=False,
                                           widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                           label=_('Filter substances by H Code'))

class OrganizationUserManagementForm(CustomForm):
    name = forms.CharField(widget=genwidgets.TextInput, required=True, label=_("Name"))
    group = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Group.objects.all(), required=True, label=_("Group"))

class SearchUserForm(CustomForm):
    user = forms.ModelChoiceField(widget=genwidgets.Select, queryset=User.objects.all(), required=True, label=_("User"))

    def __init__(self, *args, **kwargs):
        users_list = kwargs.pop('users_list')
        super(SearchUserForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.all().exclude(pk__in=users_list)


class ProfilePermissionForm(GTForm):
    user = forms.ModelChoiceField(widget=genwidgets.Select, queryset=User.objects.all(), required=True, label=_("User"))
    rol = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Rol.objects.all(), required=False,
                                         label=_("Roles"))

    def __init__(self, *args, **kwargs):
        users_list = kwargs.pop('users_list')
        super(ProfilePermissionForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.all().exclude(pk__in=users_list)


class ReservationModalForm(GTForm, ModelForm):

    class Meta:
        model = ReservedProducts
        fields = ['amount_required','initial_date', 'final_date']
        widgets = {
            'initial_date': genwidgets.DateTimeInput,
            'final_date': genwidgets.DateTimeInput,
            'amount_required': genwidgets.TextInput
        }


class TransferObjectForm(GTForm):
    amount_send = forms.CharField(widget=genwidgets.TextInput, max_length=10, label=_('Amount'),help_text='Use dot like 0.344 on decimal', required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.all(), label=_("Laboratory"), required=True)

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab=kwargs.pop('lab_send')
        super(TransferObjectForm, self).__init__(*args, **kwargs)
        profile = Profile.objects.filter(pk=users).first()
        self.fields['laboratory'].queryset = profile.laboratories


class AddObjectForm(forms.Form):
    amount = forms.CharField(widget=genwidgets.TextInput, max_length=10, help_text='Use dot like 0.344 on decimal', label=_('Amount'), required=True)
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"),required=False)
    provider = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Provider.objects.all(),
                                       label=_("Provider"),required=False)

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        super(AddObjectForm, self).__init__(*args, **kwargs)
        providers = Provider.objects.filter(laboratory__id=int(lab))
        self.fields['provider'].queryset = providers


class SubtractObjectForm(GTForm):
    discount = forms.CharField(widget=genwidgets.TextInput, max_length=10, help_text='Use dot like 0.344 on decimal', label=_('Amount'), required=True)
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text='Describe the action',label=_('Description'), required=False)

class ProfileForm(forms.Form):
    first_name = forms.CharField(widget=genwidgets.TextInput, label=_("Name"))
    last_name = forms.CharField(widget=genwidgets.TextInput, label=_("Last Name"))
    id_card = forms.CharField(widget=genwidgets.TextInput, label=_("Id Card"))
    job_position = forms.CharField(widget=genwidgets.TextInput, label=_("Job Position"))
    profile_id = forms.CharField(widget=forms.HiddenInput())

class AddTransferObjectForm(GTForm):
    shelf = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Shelf.objects.all(), label=_("Shelf"), required=True)

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        super(AddTransferObjectForm, self).__init__(*args, **kwargs)
        shelf = Shelf.objects.filter(furniture__labroom__laboratory__id=int(lab))
        self.fields['shelf'].queryset = shelf

class ProviderForm(forms.ModelForm,GTForm):

    class Meta:
        model = Provider
        fields = ['name','phone_number','email','legal_identity']
        widgets = {'name': genwidgets.TextInput,
                 'phone_number': genwidgets.TextInput,
                 'email': genwidgets.EmailMaskInput,
                 'legal_identity': genwidgets.TextInput,
                   }