from django import forms
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import CustomForm, GTForm
from djgentelella.widgets import core as genwidgets

from auth_and_perms.models import Profile
from derb.models import CustomForm as DerbCustomForm
from laboratory.models import OrganizationStructure, CommentInform, Catalog
from reservations_management.models import ReservedProducts
from sga.models import DangerIndication
from .models import Laboratory, Object, Provider, Shelf, Inform, ObjectFeatures, LaboratoryRoom, Furniture
from .utils import get_pk_org_ancestors_decendants


class ObjectSearchForm(GTForm, forms.Form):
    q = forms.ModelMultipleChoiceField(queryset=Object.objects.none(), widget=genwidgets.SelectMultiple,
                                       required=False, label=_("Search by name, code or CAS number"))

    all_labs = forms.BooleanField(widget=genwidgets.YesNoInput, required=False, label=_("All labs"))

    def __init__(self, *args, **kwargs):
        org = None
        user = None

        if 'org_pk' in kwargs:
            org=kwargs.pop('org_pk')
        if 'user' in kwargs:
            user=kwargs.pop('user')

        super(ObjectSearchForm, self).__init__(*args, **kwargs)
        if org:
            org=get_pk_org_ancestors_decendants(user, org)
            self.fields['q'].queryset = Object.objects.filter(organization__in=org, organization__organizationusermanagement__users=user).distinct()

class UserAccessForm(forms.Form):
    access = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'id': 'user_cb_'}))  # User_checkbox_id
    # For delete users. Add a delete button.


class LaboratoryCreate(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LaboratoryCreate, self).__init__(*args, **kwargs)
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
            'organization': genwidgets.HiddenInput
        }


class LaboratoryEdit(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LaboratoryEdit, self).__init__(*args, **kwargs)
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
            'organization': genwidgets.HiddenInput
        }


class H_CodeForm(GTForm, forms.Form):
    hcode = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all(), required=False,
                                           widget=genwidgets.SelectMultiple,
                                           label=_('Filter substances by H Code'))


class OrganizationUserManagementForm(GTForm):
    name = forms.CharField(widget=genwidgets.TextInput, required=True, label=_("Name"))
    group = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Group.objects.all(), required=True,
                                   label=_("Group"))


class ReservationModalForm(GTForm, ModelForm):

    def __init__(self, *args, **kwargs):
        super(ReservationModalForm, self).__init__(*args, **kwargs)
        self.fields['initial_date'].help_text = _('Entered date should be greater than current date and time')
        self.fields['final_date'].help_text = _('Entered date should be greater than current date and time')


    class Meta:
        model = ReservedProducts
        fields = ['amount_required', 'initial_date', 'final_date']
        widgets = {
            'initial_date': genwidgets.DateTimeInput,
            'final_date': genwidgets.DateTimeInput,
            'amount_required': genwidgets.TextInput
        }

class ReservedModalForm(GTForm, ModelForm):
    options = forms.IntegerField(initial=1, widget=genwidgets.HiddenInput)
    class Meta:
        model = ReservedProducts
        fields = ['amount_required', 'initial_date', 'final_date']
        widgets = {
            'initial_date': genwidgets.DateTimeInput,
            'final_date': genwidgets.DateTimeInput,
            'amount_required': genwidgets.TextInput,
        }


class TransferObjectForm(GTForm):
    amount_send = forms.CharField(widget=genwidgets.TextInput, max_length=10, label=_('Amount'),
                                  help_text='Use dot like 0.344 on decimal', required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.all(),
                                        label=_("Laboratory"), required=True)

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab = kwargs.pop('lab_send')
        org = kwargs.pop('org')
        super(TransferObjectForm, self).__init__(*args, **kwargs)
        profile = Profile.objects.filter(pk=users.profile.pk).first()
        orgs= get_pk_org_ancestors_decendants(users,org)

        self.fields['laboratory'].queryset = profile.laboratories.filter(organization__in=orgs).exclude(pk=lab)


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


class FurnitureCreateForm(forms.ModelForm, GTForm):
    class Meta:
        model = Furniture
        fields = ("name", "type")
        widgets = {
            "name": genwidgets.TextInput,
            "type": genwidgets.Select(attrs={'data-dropdownparent': '#furnitureModal',
                                             'data-placeholder': _('Select Furniture')})
        }


class RoomCreateForm(forms.ModelForm, GTForm):
    class Meta:
        model = LaboratoryRoom
        fields = '__all__'
        widgets = {
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
                   'type': genwidgets.SelectWithAdd(attrs={
                       'add_url': reverse_lazy("laboratory:add_furniture_type_catalog")}),
                   'phone_number': genwidgets.PhoneNumberMaskInput,
                   'email': genwidgets.EmailMaskInput,
                   'legal_identity': genwidgets.TextInput(attrs={'required': True}),
                   }

class InformForm(forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(InformForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields['custom_form'].queryset = DerbCustomForm.objects.filter(organization__pk=org_pk)
        else:
            self.fields['custom_form'].queryset = DerbCustomForm.objects.none()

    class Meta:
        model = Inform
        fields = ['name', 'custom_form']
        widgets = {'name': genwidgets.TextInput(attrs={'required': True}),
                   'custom_form': genwidgets.Select(),
                   }
class CommentForm(forms.ModelForm, GTForm):
    class Meta:
        model = CommentInform
        fields = ['creator', 'comment']
        widgets = {'creator': genwidgets.HiddenInput,
                   'comment': genwidgets.Textarea,
                   }


class AddOrganizationForm(GTForm, forms.ModelForm):
    class Meta:
        model = OrganizationStructure
        fields = ['name', 'parent']
        widgets={
            'name': genwidgets.TextInput,
            'parent': genwidgets.HiddenInput
        }


class CatalogForm(GTForm, forms.ModelForm):
    class Meta:
        model = Catalog
        fields = '__all__'
        widgets = {
            'key': genwidgets.HiddenInput,
            'description': genwidgets.TextInput
        }