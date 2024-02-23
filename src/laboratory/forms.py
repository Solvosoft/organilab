import re

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from auth_and_perms.models import Profile, Rol
from authentication.forms import PasswordChangeForm
from derb.models import CustomForm as DerbCustomForm
from laboratory import utils
from laboratory.models import OrganizationStructure, CommentInform, Catalog, \
    InformScheduler, RegisterUserQR, \
    ShelfObjectLimits, ShelfObject, ShelfObjectObservation, MaterialCapacity
from reservations_management.models import ReservedProducts
from sga.models import DangerIndication
from .models import Laboratory, Object, Provider, Shelf, Inform, ObjectFeatures, LaboratoryRoom, Furniture

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
                                  help_text=_('Use dot like 0.344 on decimal'), required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.all(),
                                        label=_("Laboratory"), required=True)
    mark_as_discard = forms.BooleanField(widget=genwidgets.YesNoInput, label=_("Mark as discard"), required=False)

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab = kwargs.pop('lab_send')
        org = kwargs.pop('org')
        super(TransferObjectForm, self).__init__(*args, **kwargs)
        profile = Profile.objects.filter(pk=users.profile.pk).first()
        orgs= utils.get_pk_org_ancestors_decendants(users,org)

        self.fields['laboratory'].queryset = profile.laboratories.filter(organization__in=orgs).exclude(pk=lab)


class AddObjectForm(GTForm, forms.Form):
    amount = forms.FloatField(widget=genwidgets.TextInput,  help_text=_('Use dot like 0.344 on decimal'),
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
    discount = forms.DecimalField(widget=genwidgets.TextInput, help_text=_('Use dot like 0.344 on decimal'),
                               label=_('Amount'), required=True)
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text=_('Describe the action'),
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
        exclude = ['laboratory', 'created_by']
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
        exclude = ['laboratory']
        widgets = {
            'name': genwidgets.TextInput,
            'created_by': genwidgets.HiddenInput
        }


class FurnitureForm(forms.ModelForm, GTForm):
    dataconfig = forms.CharField(
        widget=forms.HiddenInput,
        validators=[RegexValidator(
            r'^[\[\],\s"\d]*$',
            message=_("Invalid format in shelf dataconfig "),
            code='invalid_format')])
    shelfs = forms.CharField(required=False,widget=forms.HiddenInput)

    def clean_shelfs(self):
        value = self.cleaned_data['shelfs']
        shelfs = []
        if value:
            shelfs = re.findall(r'\d+', self.cleaned_data['shelfs'])
        return shelfs

    class Meta:
        model = Furniture
        fields = ("labroom", "name", "type", 'dataconfig', 'color')
        widgets = {'labroom': genwidgets.Select,
                   'name': genwidgets.TextInput,
                   'type': genwidgets.SelectWithAdd(attrs={
                       'add_url': reverse_lazy("laboratory:add_furniture_type_catalog")}),
                   'phone_number': genwidgets.PhoneNumberMaskInput,
                   'email': genwidgets.EmailMaskInput,
                   'legal_identity': genwidgets.TextInput(attrs={'required': True}),
                   'color': genwidgets.ColorInput
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
        fields = ['created_by', 'comment']
        widgets = {'created_by': genwidgets.HiddenInput,
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

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')

        if parent and not parent.active:
            raise ValidationError(_("Organization parent cannot be inactive"))

class RelOrganizationForm(GTForm):
    contentyperelobj = forms.ModelMultipleChoiceField(
        queryset=Laboratory.objects.all(),
        widget=AutocompleteSelectMultiple(url='relorgbase', attrs={
            'data-s2filter-organization': '#relorg_organization'
        }),
        label=_("Laboratories to be related to this organization")
    )

class RelOrganizationPKIntForm(GTForm):
    organization = forms.IntegerField(required=True)
    laboratory = forms.IntegerField(required=False)
    typeofcontenttype = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        org_pk = cleaned_data.get('organization')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk)

        if not organization.active:
            self.add_error("organization", _("Organization cannot be inactive"))


class CatalogForm(GTForm, forms.ModelForm):
    class Meta:
        model = Catalog
        fields = '__all__'
        widgets = {
            'key': genwidgets.HiddenInput,
            'description': genwidgets.TextInput
        }


class InformSchedulerForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['inform_template'].widget.extra_url_kwargs['pk']=org_pk

    class Meta:
        model =InformScheduler
        fields = ['organization', 'name', 'start_application_date', 'close_application_date',
                  'period_on_days', 'inform_template', 'active']
        widgets ={
            'organization': genwidgets.HiddenInput,
            'name': genwidgets.TextInput,
            'start_application_date': genwidgets.DateInput,
            'close_application_date': genwidgets.DateInput,
            'period_on_days': genwidgets.NumberInput,
            'inform_template': AutocompleteSelect('informtemplate', url_suffix='-detail'),
            'active': genwidgets.YesNoInput
        }


class InformSchedulerFormEdit(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['inform_template'].widget.extra_url_kwargs['pk']=org_pk

    class Meta:
        model =InformScheduler
        fields = ['organization', 'name', 'period_on_days', 'inform_template', 'active']
        widgets ={
            'organization': genwidgets.HiddenInput,
            'name': genwidgets.TextInput,
            'period_on_days': genwidgets.NumberInput,
            'inform_template': AutocompleteSelect('informtemplate', url_suffix='-detail'),
            'active': genwidgets.YesNoInput
        }


class RegisterUserQRForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.obj = kwargs.pop('obj', None)
        org_pk = kwargs.pop('org_pk', None)
        lab_pk = kwargs.pop('lab_pk', None)
        new_obj = kwargs.pop('new_obj', False)
        super().__init__(*args, **kwargs)

        self.fields['url'].required = False
        self.fields['organization_register'].label = _("Organization")
        org_queryset = OrganizationStructure.objects.none()
        role_queryset = OrganizationStructure.objects.none()

        if org_pk and lab_pk:
            organization = OrganizationStructure.objects.get(pk=org_pk)
            if not new_obj:
                org_queryset = utils.get_organizations_register_user(organization, lab_pk,
                                                                     self.instance.organization_register.pk)
            else:
                org_queryset = utils.get_organizations_register_user(organization, lab_pk)

            role_pk_list = utils.get_rols_from_organization(organization.pk, org=organization, rolfilters={'rol__isnull': False})
            role_queryset = Rol.objects.filter(pk__in=set(role_pk_list))

        self.fields['role'].queryset = role_queryset
        self.fields['organization_register'].queryset = org_queryset

        if new_obj:
            self.fields['code'].help_text = _("Once registration process conclude this code won't be editable.")
        else:
            self.fields['code'].disabled = True

    class Meta:
        model = RegisterUserQR
        fields = ['activate_user', 'role', 'url', 'organization_register', 'organization_creator', 'object_id',
                  'content_type', 'created_by', 'code']
        widgets = {
            'activate_user': genwidgets.YesNoInput,
            'role': genwidgets.Select,
            'organization_register': genwidgets.Select,
            'organization_creator': genwidgets.HiddenInput,
            'object_id': genwidgets.HiddenInput,
            'content_type': genwidgets.HiddenInput,
            'url': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'code': genwidgets.TextInput
        }

    def clean_code(self):
        code = self.cleaned_data['code']

        if code:
            qr_obj = RegisterUserQR.objects.filter(code=code)
            if self.obj:
                qr_obj = qr_obj.exclude(pk=self.obj.pk)

            if qr_obj.exists():
                raise ValidationError(_("This code is already exists."))
            else:
                return code


class RegisterForm(forms.ModelForm, GTForm):
    id_card = forms.CharField(widget=genwidgets.TextInput, label=_("Id Card"))
    phone_number = forms.CharField(widget=genwidgets.PhoneNumberMaskInput, label=_("Phone"))

    def __init__(self, *args, **kwargs):
        self.obj = kwargs.pop('obj', None)
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    field_order = ['first_name', 'last_name', 'email', 'phone_number', 'id_card']

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'id_card', 'phone_number']
        widgets = {
            'first_name': genwidgets.TextInput,
            'last_name': genwidgets.TextInput,
            'email': genwidgets.EmailMaskInput
        }

    def clean_email(self):
        email = self.cleaned_data['email']

        if email:
            user_obj = User.objects.filter(email=email)
            if self.obj:
                user_obj = user_obj.exclude(pk=self.obj)

            if user_obj.exists():
                raise ValidationError(_("Email address is already exists."))
            else:
                return email

class LoginForm(GTForm, forms.Form):
    username = UsernameField(widget=genwidgets.TextInput(attrs={"autofocus": True}), label=_("Username"),)
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=genwidgets.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }


class PasswordCodeForm(PasswordChangeForm):
    code = forms.CharField(widget=genwidgets.TextInput, required=True, max_length=4, label=_("Code"))

    def __init__(self, *args, **kwargs):
        self.code = kwargs.pop('code', None)
        self.user = kwargs.pop('user', None)
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']

        if code != self.code:
            raise ValidationError(_("Code didn't match."))
        else:
            return code

class ShelfObjectOptions(GTForm, forms.Form):
    lab = forms.ModelChoiceField(queryset=Laboratory.objects.all(), required=True)
    options = forms.IntegerField(required=True)
    shelf_object = forms.IntegerField(required=True)

class ShelfObjectListForm(GTForm, forms.Form):
    lab = forms.ModelChoiceField(queryset=Laboratory.objects.all(), required=True)
    id = forms.IntegerField(required=True)


#VALIDATE DATA FORMS
class FurnitureLabRoomForm(forms.Form):
    labroom = forms.IntegerField(required=True)


class ValidateShelfForm(forms.Form):
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.all(), required=True)
    objecttype = forms.ChoiceField(choices=(
        ("0", _('Reactive')),
        ("1", _('Material')),
        ("2", _('Equipment'))
    )
, required=True)


class ReservedProductsForm(forms.Form):
    obj = forms.IntegerField(required=True)
    user = forms.IntegerField(required=True)
    status = forms.IntegerField(required=True)
    initial_date = forms.DateTimeField(required=True)


class ValidateShelfUnitForm(GTForm):
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.all(), required=True)


class ShelfObjectStatusForm(GTForm, forms.ModelForm):
    description = forms.CharField(widget=genwidgets.Textarea)

    def __init__(self, *args, **kwargs):
        org_pk=kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}),
            help_text='<a class="add_status float-end fw-bold m-2"><i class="fa fa-plus"></i> %s</a>'%(_("New status")))

    class Meta:
        model = ShelfObject
        fields = ['status']



class ObservationShelfObjectForm(GTForm, forms.ModelForm):

    class Meta:
        model=ShelfObjectObservation
        exclude=['shelf_object', 'created_by']
        widgets={
            'action_taken': genwidgets.TextInput,
            'description': genwidgets.Textarea
        }


class MaterialCapacityObjectForm(GTForm,forms.Form):
    capacity = forms.FloatField(required=False, widget=genwidgets.TextInput, min_value=settings.DEFAULT_MIN_QUANTITY, label=_("Capacity"))
    capacity_measurement_unit = forms.ModelChoiceField(queryset=Catalog.objects.filter(key='units'),
                                                       required=False,
                                                       widget=genwidgets.Select(),
                                                       label=_("Capacity measurement unit"))
    object = forms.ModelChoiceField(queryset=Object.objects.all(), required=False,
                                    widget=genwidgets.HiddenInput)


class ObjectForm(MaterialCapacityObjectForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        self.request = None
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        instance = None
        if 'instance' in kwargs:
            instance = kwargs.get('instance')
        data_type = None
        if 'data' in kwargs:
            data_type = kwargs.get('data').get('type')

        super(ObjectForm, self).__init__(*args, **kwargs)

        if self.request and not self.initial['type']:
            if 'type_id' in self.request.GET:
                self.type_id = self.request.GET.get('type_id', '')
                if self.type_id:
                    self.fields['type'] = forms.CharField(
                        initial=self.type_id,
                        widget=forms.HiddenInput()
                    )
                data_type = self.type_id
        if data_type != Object.MATERIAL:
            self.fields.pop('object')
            self.fields.pop('capacity')
            self.fields.pop('capacity_measurement_unit')
            self.fields.pop('is_container')
        else:
            self.fields['object'].required = False
            self.fields['is_container'].initial = True

        if data_type == Object.EQUIPMENT:
            self.fields['model'].required = True

        else:
            self.fields['model'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['serie'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['plaque'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )

    def clean(self):
        cleaned_data = super().clean()
        is_container = cleaned_data.get('is_container')
        object_type = cleaned_data.get('type')
        capacity = cleaned_data.get('capacity')
        capacity_unit = cleaned_data.get('capacity_measurement_unit')

        if object_type==Object.MATERIAL:
            if is_container:
                if capacity == None:
                    self.add_error('capacity',_("This field is required."))
                elif capacity<0:
                    self.add_error('capacity',_("Ensure this value is greater than or equal to 1e-07."))
                if capacity_unit == None:
                    self.add_error('capacity_measurement_unit',_('This field is required.'))
    class Meta:
        model = Object
        exclude = ['organization', 'created_by']
        widgets = {
            'features': genwidgets.SelectMultiple(),
            'code': genwidgets.TextInput,
            'name': genwidgets.TextInput,
            'synonym':  genwidgets.TextInput,
            'is_public': genwidgets.YesNoInput,
            'description': genwidgets.Textarea,
            'model': genwidgets.TextInput,
            'serie': genwidgets.TextInput,
            'plaque': genwidgets.TextInput,
            "type": genwidgets.HiddenInput,
            "is_container": genwidgets.YesNoInput
        }


class ObjectUpdateForm(MaterialCapacityObjectForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):

        self.request = None
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        instance = None
        if 'instance' in kwargs:
            instance = kwargs.get('instance')
        data_type = None
        if 'data' in kwargs:
            data_type = kwargs.get('data').get('type')

        super(ObjectUpdateForm, self).__init__(*args, **kwargs)

        if self.request:
            if 'type_id' in self.request.GET:
                self.type_id = self.request.GET.get('type_id', '')
                if self.type_id:
                    self.fields['type'] = forms.CharField(
                        initial=self.type_id,
                        widget=forms.HiddenInput()
                    )
                data_type = self.type_id
        if data_type != Object.MATERIAL:
            self.fields.pop('object')
            self.fields.pop('capacity')
            self.fields.pop('capacity_measurement_unit')
            self.fields.pop('is_container')
        else:
            self.fields['object'].required = False

            if instance:
                if hasattr(instance,'materialcapacity'):
                    self.fields['object'].initial = (instance.id)
                    self.fields['capacity'].initial = instance.materialcapacity.capacity
                    self.fields['capacity_measurement_unit'].initial = (
                        instance.materialcapacity.capacity_measurement_unit.id)

        if data_type == Object.EQUIPMENT:
            self.fields['model'].required = True

        else:
            self.fields['model'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['serie'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['plaque'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )

    def clean(self):
        cleaned_data = super().clean()
        is_container = cleaned_data.get('is_container')
        object_type = cleaned_data.get('type')
        capacity = cleaned_data.get('capacity')
        capacity_unit = cleaned_data.get('capacity_measurement_unit')
        get_instance_is_container = self.instance.is_container
        shelfobjects = ShelfObject.objects.filter(
            container__object=self.instance)

        if object_type==Object.MATERIAL:
            if get_instance_is_container and is_container==False and shelfobjects:
                self.add_error('is_container','This field cannot be updated because the material is used as a container for at least one reactive.')
            if is_container:
                if capacity == None:
                    self.add_error('capacity',_("This field is required."))
                elif capacity<0:
                    self.add_error('capacity',_("Ensure this value is greater than or equal to 1e-07."))
                if capacity_unit == None:
                    self.add_error('capacity_measurement_unit',_('This field is required.'))
    class Meta:
        model = Object
        exclude = ['organization', 'created_by']
        widgets = {
            'features': genwidgets.SelectMultiple(),
            'code': genwidgets.TextInput,
            'name': genwidgets.TextInput,
            'synonym':  genwidgets.TextInput,
            'is_public': genwidgets.YesNoInput,
            'description': genwidgets.Textarea,
            'model': genwidgets.TextInput,
            'serie': genwidgets.TextInput,
            'plaque': genwidgets.TextInput,
            "type": genwidgets.HiddenInput,
            "is_container": genwidgets.YesNoInput
        }


class ChangeOrganizationParentForm(GTForm, forms.ModelForm):
    class Meta:
        model = OrganizationStructure
        fields = ['parent']
        widgets={
            'parent': genwidgets.HiddenInput
        }

    def clean(self):
        if not self.instance.active:
            raise ValidationError(_("Organization cannot be inactive"))
