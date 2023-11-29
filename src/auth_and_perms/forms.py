from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from django_otp.forms import OTPTokenForm
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelectMultiple, AutocompleteSelect

from auth_and_perms.models import Rol, Profile
from laboratory.models import Laboratory, OrganizationStructure, Object


class AddUserForm(GTForm, forms.Form):
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(),
                                           label=_("Users"),
                                           widget=AutocompleteSelectMultiple(
                                               'orguserbase'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['users'].required = False


class AddRolForm(GTForm, forms.Form):
    rols = forms.ModelMultipleChoiceField(queryset=Rol.objects.all(), label=_("Rols"),
                                          widget=AutocompleteSelectMultiple(
                                              'roluserorgbase'), required=True)


class AddProfileRolForm(GTForm, forms.Form):
    rols = forms.ModelMultipleChoiceField(queryset=Rol.objects.none(), label=_("Rols"),
                                          widget=AutocompleteSelectMultiple('rolbase'),
                                          required=True)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    contentobj_pk = forms.CharField(widget=forms.HiddenInput(), required=False)
    org_pk = forms.CharField(widget=forms.HiddenInput(), required=True)


class CreationUserOrganization(UserCreationForm, GTForm):
    organization_name = forms.CharField(max_length=255, widget=genwidgets.TextInput,
                                        label=_('Organization name'))
    validation_method = forms.ChoiceField(
        choices=((1, 'OTPT'), (2, _('Digital signature'))),
        # choices=((1, 'OTPT'),),
        widget=genwidgets.RadioSelect,
        label=_('Validation method')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = genwidgets.PasswordInput(
            attrs={"autocomplete": _("new-password")})
        self.fields['password2'].widget = genwidgets.PasswordInput(
            attrs={"autocomplete": _("new-password")})
        self.fields['username'].label = _("Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields
        widgets = {
            'username': genwidgets.EmailInput

        }


# from django_otp.views import LoginView
class AddProfileForm(OTPTokenForm, GTForm):
    first_name = forms.CharField(label=_("First name"), max_length=150,
                                 widget=genwidgets.TextInput)
    last_name = forms.CharField(label=_("Last name"), max_length=150,
                                widget=genwidgets.TextInput)
    email = forms.EmailField(label=_("Email address"), widget=genwidgets.EmailInput)
    phone_number = forms.CharField(label=_('Phone'), max_length=25,
                                   widget=genwidgets.TextInput)
    id_card = forms.CharField(label=_('Identification'), max_length=100,
                              widget=genwidgets.TextInput)
    job_position = forms.CharField(label=_('Job Position'), max_length=100,
                                   widget=genwidgets.TextInput)

    field_order = [
        'first_name', 'last_name', 'email', 'phone_number', 'id_card', 'job_position',
        'otp_device',
        'otp_challenge', 'otp_token'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['otp_device'].widget = forms.HiddenInput()
        self.fields['otp_challenge'].widget = forms.HiddenInput()
        self.fields['otp_token'].widget = genwidgets.TextInput()


class AddProfileDigitalSignatureForm(GTForm):
    first_name = forms.CharField(label=_("First name"), max_length=150,
                                 widget=genwidgets.TextInput)
    last_name = forms.CharField(label=_("Last name"), max_length=150,
                                widget=genwidgets.TextInput)
    email = forms.EmailField(label=_("Email address"), widget=genwidgets.EmailInput)
    phone_number = forms.CharField(label=_('Phone'), max_length=25,
                                   widget=genwidgets.TextInput)
    id_card = forms.CharField(label=_('Identification'), max_length=100,
                              widget=genwidgets.TextInput,
                              help_text=_(
                                  'It will used to login when you want to login with digital signature'))
    job_position = forms.CharField(label=_('Job Position'), max_length=100,
                                   widget=genwidgets.TextInput)
    ds_transaction = forms.CharField(widget=genwidgets.HiddenInput, max_length=20)

    field_order = [
        'first_name', 'last_name', 'email', 'phone_number', 'id_card', 'job_position',
        'ds_transaction'
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


class OrganizationActions(GTForm):
    ACTIONS = (
        (1, _('Inactive organization')),
        (2, _('Clone organization')),
        (3, _('Change organization name')),
    )
    actions = forms.ChoiceField(widget=genwidgets.Select, choices=ACTIONS, label=_("Actions"))
    action_organization = forms.ModelChoiceField(
        queryset=OrganizationStructure.objects.all(),
        widget=genwidgets.HiddenInput)
    name = forms.CharField(widget=genwidgets.TextInput, required=False, label=_("Name"))

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        actions = cleaned_data.get('actions')
        organization = cleaned_data.get('action_organization')

        if not organization.active:

            if actions in [1, 3]:

                if actions == 3 and not name:
                    self.add_error('name', 'Name not found')

                self.add_error("action_organization", _("Organization cannot be inactive"))


class OrganizationActionsWithoutInactive(OrganizationActions):
    ACTIONS = (
        (2, _('Clone organization')),
        (3, _('Change organization name')),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['actions'].choices = self.ACTIONS

class OrganizationActionsClone(GTForm):
    ACTIONS = (
        (2, _('Clone organization')),
    )
    actions = forms.ChoiceField(widget=genwidgets.Select, choices=ACTIONS, label=_("Actions"))
    action_organization = forms.ModelChoiceField(
        queryset=OrganizationStructure.objects.all(),
        widget=genwidgets.HiddenInput)

class ContentypeForm(GTForm, forms.Form):
    organization = forms.IntegerField()
    contentyperelobj = forms.ModelMultipleChoiceField(queryset=Laboratory.objects.all())


class ProfileGroupForm(GTForm):
    profile = forms.ModelChoiceField(queryset=User.objects.all(),
                                     widget=AutocompleteSelect('usersbyorg', attrs={
                                         'data-s2filter-organization': '.nodeorg:checked'
                                     })
                                     )
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(),
                                            widget=genwidgets.SelectMultiple)
    organization = forms.IntegerField(widget=genwidgets.HiddenInput)


class OrgTreeForm(GTForm):
    organization = forms.ModelChoiceField(queryset=OrganizationStructure.objects.all(),
                                          widget=AutocompleteSelect('orgtree')
                                          )
class SearchObjByOrgForm(GTForm):
    object = forms.ModelChoiceField(queryset=Object.objects.all(),
                                    widget=AutocompleteSelect('objbyorg', attrs={
                                        'data-s2filter-organization': '#id_organization'
                                    }), label=_("Search by object")
                                    )

class SearchShelfObjectViewsetForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=OrganizationStructure.objects.all())
    object = forms.ModelChoiceField(queryset=Object.objects.all())
