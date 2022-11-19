from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_otp.forms import OTPTokenForm
from djgentelella.forms.forms import GTForm
from djgentelella.widgets.selects import AutocompleteSelectMultiple
from djgentelella.widgets import core as genwidgets
from auth_and_perms.models import Rol


class AddUserForm(GTForm, forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), label=_("Users"),
                                           widget=AutocompleteSelectMultiple('orguserbase'))


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
    organization_name = forms.CharField(max_length=255, widget=genwidgets.TextInput)
    validation_method = forms.ChoiceField(
        choices=((1, 'OTPT' ),(2, 'Digital Signature')),
        #choices=((1, 'OTPT'),),
        widget=genwidgets.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget=genwidgets.PasswordInput(attrs={"autocomplete": _("new-password")})
        self.fields['password2'].widget=genwidgets.PasswordInput(attrs={"autocomplete": _("new-password")})

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields
        widgets = {
            'username': genwidgets.TextInput

        }
#from django_otp.views import LoginView
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
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['otp_device'].widget=forms.HiddenInput()
        self.fields['otp_challenge'].widget=forms.HiddenInput()
        self.fields['otp_token'].widget=genwidgets.TextInput()


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