from django import forms
from django.contrib.auth.models import Group, User
from django.core.validators import RegexValidator
from djgentelella.forms.forms import CustomForm

from auth_and_perms.models import Profile, Rol
from sga.models import DangerIndication
from .models import Laboratory, Object, Provider, Shelf, ObjectFeatures, LaboratoryRoom, Furniture
from reservations_management.models import ReservedProducts
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from laboratory.models import OrganizationStructure
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from django.forms import ModelForm

class ObjectSearchForm(CustomForm, forms.Form):
    q = forms.ModelMultipleChoiceField(queryset=Object.objects.all(), widget=genwidgets.SelectMultiple,
                                       required=False, label=_("Search by name, code or CAS number"))

    all_labs = forms.BooleanField(widget=genwidgets.YesNoInput, required=False, label=_("All labs"))


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


class LaboratoryCreate(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(LaboratoryCreate, self).__init__(*args, **kwargs)
        self.fields['organization'].queryset = \
            OrganizationStructure.os_manager.filter_user(user)
        self.fields['geolocation'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Laboratory
        fields = ['name', 'phone_number', 'location',
                  'geolocation', 'organization']
        widgets = {
            'name': genwidgets.TextInput,
            'phone_number': genwidgets.TextInput,
            'location': genwidgets.TextInput,
            'geolocation': genwidgets.TextInput,
            'organization': genwidgets.Select
        }


class LaboratoryEdit(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(LaboratoryEdit, self).__init__(*args, **kwargs)
        self.fields['organization'].queryset = \
            OrganizationStructure.os_manager.filter_user(user)
        self.fields['geolocation'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Laboratory
        fields = ['name', 'coordinator', 'unit', 'phone_number', 'email', 'location',
                  'geolocation', 'organization']
        widgets = {
            'name': genwidgets.TextInput,
            'coordinator': genwidgets.TextInput,
            'unit': genwidgets.TextInput,
            'phone_number': genwidgets.TextInput,
            'email': genwidgets.EmailInput,
            'location': genwidgets.TextInput,
            'geolocation': genwidgets.TextInput,
            'organization': genwidgets.Select
        }


class H_CodeForm(GTForm, forms.Form):
    hcode = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all(), required=False,
                                           widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
                                           label=_('Filter substances by H Code'))


class OrganizationUserManagementForm(GTForm):
    name = forms.CharField(widget=genwidgets.TextInput, required=True, label=_("Name"))
    group = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Group.objects.all(), required=True,
                                   label=_("Group"))


class SearchUserForm(GTForm):
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
        fields = ['amount_required', 'initial_date', 'final_date']
        widgets = {
            'initial_date': genwidgets.DateTimeInput,
            'final_date': genwidgets.DateTimeInput,
            'amount_required': genwidgets.TextInput
        }


class TransferObjectForm(GTForm):
    amount_send = forms.CharField(widget=genwidgets.TextInput, max_length=10, label=_('Amount'),
                                  help_text='Use dot like 0.344 on decimal', required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.all(),
                                        label=_("Laboratory"), required=True)

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab = kwargs.pop('lab_send')
        super(TransferObjectForm, self).__init__(*args, **kwargs)
        profile = Profile.objects.filter(pk=users).first()

        self.fields['laboratory'].queryset = profile.laboratories.all().exclude(pk=lab)


class AddObjectForm(GTForm, forms.Form):
    amount = forms.CharField(widget=genwidgets.TextInput, max_length=10, help_text='Use dot like 0.344 on decimal',
                             label=_('Amount'), required=True)
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"), required=False)
    provider = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Provider.objects.all(),
                                      label=_("Provider"), required=False)

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        super(AddObjectForm, self).__init__(*args, **kwargs)
        providers = Provider.objects.filter(laboratory__id=int(lab))
        self.fields['provider'].queryset = providers


class SubtractObjectForm(GTForm):
    discount = forms.CharField(widget=genwidgets.TextInput, max_length=10, help_text='Use dot like 0.344 on decimal',
                               label=_('Amount'), required=True)
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text='Describe the action',
                                  label=_('Description'), required=False)


class ProfileForm(GTForm, forms.Form):
    first_name = forms.CharField(widget=genwidgets.TextInput, label=_("Name"))
    last_name = forms.CharField(widget=genwidgets.TextInput, label=_("Last Name"))
    id_card = forms.CharField(widget=genwidgets.TextInput, label=_("Id Card"))
    job_position = forms.CharField(widget=genwidgets.TextInput, label=_("Job Position"))
    profile_id = forms.CharField(widget=forms.HiddenInput())


class AddTransferObjectForm(GTForm):
    shelf = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Shelf.objects.all(), label=_("Shelf"),
                                   required=True)

    def __init__(self, *args, **kwargs):
        lab = kwargs.pop('lab')
        super(AddTransferObjectForm, self).__init__(*args, **kwargs)
        shelf = Shelf.objects.filter(furniture__labroom__laboratory__id=int(lab))
        self.fields['shelf'].queryset = shelf


class ProviderForm(forms.ModelForm, GTForm):
    class Meta:
        model = Provider
        fields = ['name', 'phone_number', 'email', 'legal_identity']
        widgets = {'name': genwidgets.TextInput(attrs={'required': True}),
                   'phone_number': genwidgets.PhoneNumberMaskInput,
                   'email': genwidgets.EmailMaskInput,
                   'legal_identity': genwidgets.TextInput(attrs={'required': True}),
                   }

class ObjectFeaturesForm(forms.ModelForm, GTForm):
    class Meta:
        model = ObjectFeatures
        fields = '__all__'
        widgets = {
            'name': genwidgets.TextInput(),
            'description': genwidgets.Textarea()
        }

class LaboratoryRoomForm(forms.ModelForm, GTForm):
    class Meta:
        model = LaboratoryRoom
        fields = '__all__'
        widgets = {
            'name': genwidgets.TextInput(),
            'legal_identity': genwidgets.NumberInput,
            }



class FurnitureCreateForm(forms.ModelForm,GTForm):
    class Meta:
        model = Furniture
        fields = ("name", "type")
        widgets = {
            "name": genwidgets.TextInput,
            "type": genwidgets.Select(attrs={'data-dropdownparent': '#furnitureModal',
                                             'data-placeholder': _('Select Furniture')})
        }

class RoomCreateForm(forms.ModelForm,GTForm):
    class Meta:
        model = LaboratoryRoom
        fields = '__all__'
        widgets={
            'name': genwidgets.TextInput
        }

class FurnitureForm(forms.ModelForm, GTForm):
    dataconfig = forms.CharField(
        widget=forms.HiddenInput,
        validators=[RegexValidator(
            r'^[\[\],\s"\d]*$',
            message=_("Invalid format in shelf dataconfig "),
            code='invalid_format')])

    class Meta:
        model = Furniture
        fields = ("labroom", "name", "type", 'dataconfig')
        widgets = {'labroom': genwidgets.Select,
                   'name': genwidgets.TextInput,
                   'type': genwidgets.Select(attrs={'id':'select_furniture'}),
                   }