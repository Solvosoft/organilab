from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_otp.forms import OTPTokenForm
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelectMultiple, AutocompleteSelect

from auth_and_perms.models import Rol
from laboratory.models import Laboratory, OrganizationStructure


class AddUserForm(GTForm, forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label=_("Users"),
                                           widget=AutocompleteSelectMultiple('orguserbase'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['users'].required = False


class AddRolForm(GTForm, forms.Form):
    rols = forms.ModelMultipleChoiceField(queryset=Rol.objects.all(), label=_("Rols"),
                                          widget=AutocompleteSelectMultiple('roluserorgbase'), required=True)


class AddProfileRolForm(GTForm, forms.Form):
    rols = forms.ModelMultipleChoiceField(queryset=Rol.objects.none(), label=_("Rols"),
                                          widget=AutocompleteSelectMultiple('rolbase'), required=True)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    org_pk = forms.CharField(widget=forms.HiddenInput(), required=True)


class CreationUserOrganization(UserCreationForm, GTForm):
    organization_name = forms.CharField(max_length=255, widget=genwidgets.TextInput, label=_('Organization name'))
    validation_method = forms.ChoiceField(
        choices=((1, 'OTPT'), (2, _('Digital signature'))),
        # choices=((1, 'OTPT'),),
        widget=genwidgets.RadioSelect,
        label=_('Validation method')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = genwidgets.PasswordInput(attrs={"autocomplete": _("new-password")})
        self.fields['password2'].widget = genwidgets.PasswordInput(attrs={"autocomplete": _("new-password")})
        self.fields['username'].label = _("Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields
        widgets = {
            'username': genwidgets.EmailInput

        }


# from django_otp.views import LoginView
class AddProfileForm(OTPTokenForm, GTForm):
    first_name = forms.CharField(label=_("First name"), max_length=150, widget=genwidgets.TextInput)
    last_name = forms.CharField(label=_("Last name"), max_length=150, widget=genwidgets.TextInput)
    email = forms.EmailField(label=_("Email address"), widget=genwidgets.EmailInput)
    phone_number = forms.CharField(label=_('Phone'), max_length=25, widget=genwidgets.TextInput)
    id_card = forms.CharField(label=_('Identification'), max_length=100, widget=genwidgets.TextInput)
    job_position = forms.CharField(label=_('Job Position'), max_length=100, widget=genwidgets.TextInput)

    field_order = [
        'first_name', 'last_name', 'email', 'phone_number', 'id_card', 'job_position', 'otp_device',
        'otp_challenge', 'otp_token'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['otp_device'].widget = forms.HiddenInput()
        self.fields['otp_challenge'].widget = forms.HiddenInput()
        self.fields['otp_token'].widget = genwidgets.TextInput()


class AddProfileDigitalSignatureForm(GTForm):
    first_name = forms.CharField(label=_("First name"), max_length=150, widget=genwidgets.TextInput)
    last_name = forms.CharField(label=_("Last name"), max_length=150, widget=genwidgets.TextInput)
    email = forms.EmailField(label=_("Email address"), widget=genwidgets.EmailInput)
    phone_number = forms.CharField(label=_('Phone'), max_length=25, widget=genwidgets.TextInput)
    id_card = forms.CharField(label=_('Identification'), max_length=100, widget=genwidgets.TextInput,
                              help_text=_('It will used to login when you want to login with digital signature'))
    job_position = forms.CharField(label=_('Job Position'), max_length=100, widget=genwidgets.TextInput)
    ds_transaction = forms.CharField(widget=genwidgets.HiddenInput, max_length=20)

    field_order = [
        'first_name', 'last_name', 'email', 'phone_number', 'id_card', 'job_position', 'ds_transaction'
    ]


class LaboratoryOfOrganizationForm(GTForm):
    laboratories = forms.ModelMultipleChoiceField(queryset=Laboratory.objects.all(),
                                                  widget=AutocompleteSelect(
                                                      'laborgbase', attrs={
                                                          'data-s2filter-organization': '.nodeorg:checked'})
                                                  )


# no visible
class LaboratoryAndOrganizationForm(forms.Form):
    laboratory = forms.ModelChoiceField(queryset=Laboratory.objects.all())
    organization = forms.ModelChoiceField(queryset=OrganizationStructure.objects.all())


class OrganizationForViewsetForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=OrganizationStructure.objects.all())


class ProfileListForm(GTForm):
    profile = forms.ModelChoiceField(queryset=User.objects.all(),
                                     widget=AutocompleteSelect('laborguserbase', attrs={
                                         'data-s2filter-organization': '.nodeorg:checked',
                                         'data-s2filter-laboratory': '#id_laboratories',
                                         'data-s2filter-typeofcontenttype': '#id_typeofcontenttype',
                                         'data-dropdownparent': '#relprofilelabmodal'
                                     })
                                     )


class ContentypeForm(GTForm, forms.Form):
    organization = forms.IntegerField()
    contentyperelobj = forms.ModelMultipleChoiceField(queryset=Laboratory.objects.all())
