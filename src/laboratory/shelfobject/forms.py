from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.files import FileChunkedUpload
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple
from auth_and_perms.models import Profile, Rol
from laboratory import utils
from laboratory.models import Laboratory, Provider, Shelf, Catalog, ShelfObject, Object, \
    LaboratoryRoom, Furniture, ShelfObjectMaintenance, ShelfObjectLog, \
    ShelfObjectCalibrate, ShelfObjectGuarantee, ShelfObjectTraining, \
    ShelfObjectEquipmentCharacteristics, OrganizationStructure
from reservations_management.models import ReservedProducts
from laboratory.shelfobject.serializers import \
    TransferInShelfObjectApproveWithContainerSerializer, ContainerSerializer


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
    amount = forms.FloatField(widget=genwidgets.TextInput, help_text=_('Use dot like 0.344 on decimal'), label=_('Amount'))
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"), required=False)
    provider = forms.ModelChoiceField(queryset=Provider.objects.all(), label=_("Provider"), required=False,
                                      widget=AutocompleteSelect("provider", attrs={
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization',
                                   })
                                      )
    shelf_object = forms.IntegerField(widget=forms.HiddenInput)

class TransferOutShelfObjectForm(GTForm):
    amount_to_transfer = forms.FloatField(widget=genwidgets.NumberInput, label=_('Amount'),
                                          help_text=_('Use dot like 0.344 on decimal'), required=True)
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.none(),
                                        label=_("Laboratory"), required=True)
    mark_as_discard = forms.BooleanField(widget=genwidgets.YesNoInput, required=False, label=_("Mark as discard"))

    def __init__(self, *args, **kwargs):
        users = kwargs.pop('users')
        lab = kwargs.pop('lab_send')
        org = kwargs.pop('org')
        super(TransferOutShelfObjectForm, self).__init__(*args, **kwargs)
        orgs = utils.get_pk_org_ancestors_decendants(users, org)

        self.fields['laboratory'].queryset = users.profile.laboratories.filter(organization__in=orgs).exclude(pk=lab)

class DecreaseShelfObjectForm(GTForm):
    amount = forms.DecimalField(widget=genwidgets.TextInput, help_text=_('Use dot like 0.344 on decimal'),
                                label=_('Amount'))
    description = forms.CharField(widget=genwidgets.TextInput, max_length=255, help_text='Describe the action',
                                  label=_('Description'), required=False)
    shelf_object = forms.IntegerField(widget=forms.HiddenInput)

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
                                       'data-s2filter-shelf': '#id_shelf',
                                       'data-s2filter-organization': '#id_organization',
                                       'data-s2filter-laboratory': '#id_laboratory'
                                   }), help_text=_("This select only shows shelves with same measurement unit than current object")
                                   )
    shelf_object = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        group_name = kwargs.pop('group_name')
        super(MoveShelfObjectForm, self).__init__(*args, **kwargs)

        self.fields["lab_room"] = forms.ModelChoiceField(
            queryset=LaboratoryRoom.objects.all(), label=_("Laboratory Room"),
            widget=AutocompleteSelect("lab_room", attrs={
                'data-related': 'true',
                'data-pos': 0,
                'data-groupname': group_name,
                'data-s2filter-shelfobject': '#id_shelfobject',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-laboratory': '#id_laboratory'
            })
        )

        self.fields["furniture"] = forms.ModelChoiceField(
            queryset=Furniture.objects.all(), label=_("Furniture"),
            widget=AutocompleteSelect("furniture", attrs={
                'data-related': 'true',
                'data-pos': 1,
                'data-groupname': group_name,
                'data-s2filter-shelfobject': '#id_shelfobject',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-laboratory': '#id_laboratory'
            })
        )

        self.fields["shelf"] = forms.ModelChoiceField(
            queryset=Shelf.objects.all(), label=_("Shelf"),
            widget=AutocompleteSelect("shelf", attrs={
                'data-related': 'true',
                'data-pos': 2,
                'data-groupname': group_name,
                'data-s2filter-shelfobject': '#id_shelfobject',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-laboratory': '#id_laboratory'
            }), help_text=_(
                "This select only shows shelves with some of the following features: "
                "<br>1) Infinity quantity capacity and not defined measurement unit. "
                "<br>2) Infinity quantity capacity and same measurement unit than selected shelf object. "
                "<br>3) Same measurement unit than selected shelf object and available capacity in the shelf.")
        )


class ShelfObjectExtraFields(GTForm, forms.Form):
    objecttype = forms.IntegerField(widget=genwidgets.HiddenInput, min_value=0, max_value=3, required=True)
    without_limit = forms.BooleanField(widget=genwidgets.CheckboxInput(attrs={'class': 'check_limit'}),
                                       label=_('Unlimited'), initial=True)
    minimum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Minimum Limit"))
    maximum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Maximum Limit"))
    expiration_date = forms.DateField(widget=genwidgets.DateInput, required=False, label=_("Expiration date"))



class ShelfObjectMaterialForm(ShelfObjectExtraFields, forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch',
                                      attrs={
                                          'data-dropdownparent': "#material_form",
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization',
                                          'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
                                      }),
            label="Material")


        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#material_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "marked_as_discard",
                  "description"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'description': genwidgets.Textarea,
            'marked_as_discard': genwidgets.CheckboxInput
        }

class ShelfObjectRefuseMaterialForm(ShelfObjectExtraFields,GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label="Material")

        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0
        self.fields['marked_as_discard'].initial=True

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "marked_as_discard",
                  "description"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'description': genwidgets.Textarea,
            'marked_as_discard': forms.HiddenInput
        }


class EquipmentCharacteristicForm(forms.Form):
    provider = forms.ModelChoiceField(queryset=Provider.objects.all(),widget=genwidgets.Select, label=_("Provider"))
    authorized_roles_to_use_equipment = forms.ModelMultipleChoiceField(queryset=Rol.objects.none(),
                                                                       widget=genwidgets.SelectMultiple,
                                                                       label=_("Authorized roles to use equipment"))
    equipment_price = forms.FloatField(initial=0.0, label=_("Price"), widget=genwidgets.TextInput,
                                       help_text=_('Use dot like 0.344 on decimal'))
    purchase_equipment_date = forms.DateField(widget=genwidgets.DateInput,label=_("Purchase Date"))
    delivery_equipment_date = forms.DateField(widget=genwidgets.DateInput,label=_("Delivery Date"))
    have_guarantee = forms.BooleanField(initial=False, widget=genwidgets.YesNoInput, label=_("Has guarantee?"))
    contract_of_maintenance = forms.FileField(widget=FileChunkedUpload, label=_("Contract of maintenance"))
    available_to_use = forms.BooleanField(initial=False, widget=genwidgets.YesNoInput, label=_("Is available to use?"))
    first_date_use = forms.DateField(widget=genwidgets.DateInput,  label=_("First date use"))
    notes = forms.CharField(widget=genwidgets.Textarea, label=_("Note"))

class ShelfObjectEquipmentForm(EquipmentCharacteristicForm,forms.ModelForm,GTForm):
    objecttype = forms.IntegerField(widget=genwidgets.HiddenInput, min_value=0, max_value=3, required=True)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch',
                                      attrs={
                                          'data-dropdownparent': "#equipment_form",
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization',
                                          'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
                                      }),
            label=_("Equipment"))

        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0
        self.fields['provider'] = forms.ModelChoiceField(
            queryset=Provider.objects.all(),
            label= _("Provider"),
            widget=AutocompleteSelect('object_providers', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-object': '#id_ef-object',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }))
        self.fields['authorized_roles_to_use_equipment'] = forms.ModelChoiceField(
            queryset=Rol.objects.all(),
            label= _("Authorized roles to use equipment"),
            widget=AutocompleteSelectMultiple('organization_roles', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-organization': '#id_organization'
            }))

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "limit_quantity", "marked_as_discard", "description"]
        exclude =['quantity']
        widgets = {
            'shelf': forms.HiddenInput,
            'limit_quantity': forms.HiddenInput,
            'description': genwidgets.Textarea,
            'marked_as_discard': genwidgets.CheckboxInput
        }

class ShelfObjectRefuseEquipmentForm(EquipmentCharacteristicForm, GTForm, forms.ModelForm):
    objecttype = forms.IntegerField(widget=genwidgets.HiddenInput, min_value=0, max_value=3, required=True)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Equipment"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0
        self.fields['provider'] = forms.ModelChoiceField(
            queryset=Provider.objects.all(),
            label= _("Provider"),
            widget=AutocompleteSelect('object_providers', attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-object': '#id_erf-object',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }))
        self.fields['authorized_roles_to_use_equipment'] = forms.ModelChoiceField(
            queryset=Rol.objects.all(),
            label= _("Authorized roles to use equipment"),
            widget=AutocompleteSelectMultiple('organization_roles', attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-organization': '#id_organization'
            }))


    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "limit_quantity", "marked_as_discard",
                  "description"]
        exclude = ["quantity"]
        widgets = {
            'shelf': forms.HiddenInput,
             'limit_quantity': forms.HiddenInput,
            'description': genwidgets.Textarea,
            'marked_as_discard': forms.HiddenInput
        }


class ValidateShelfUnitForm(GTForm):
    shelf = forms.ModelChoiceField(queryset=Shelf.objects.all(), required=True)

class ShelfObjectStatusForm(GTForm, forms.ModelForm):
    description = forms.CharField(widget=genwidgets.Textarea, label=_("Description"))

    def __init__(self, *args, **kwargs):
        org_pk=kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search',attrs={
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold m-2"><i class="fa fa-plus"></i> %s</a>'%(_("New status")),label=_("Status"))


    class Meta:
        model = ShelfObject
        fields = ['status']


class ContainerForm(GTForm):
    container_select_option = forms.ChoiceField(widget=genwidgets.RadioVerticalSelect, choices=ContainerSerializer.CONTAINER_SELECT_CHOICES,
                                                label=_("Container Options"))
    container_for_cloning = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Object.objects.none(), label=_("Container"))
    available_container = forms.ModelChoiceField(widget=genwidgets.Select, queryset=ShelfObject.objects.none(), label=_("Container"))

    def __init__(self, *args, **kwargs):
        modal_id = kwargs.pop('modal_id')
        set_container_advanced_options = kwargs.pop('set_container_advanced_options', False)
        super(ContainerForm, self).__init__(*args, **kwargs)

        if set_container_advanced_options:
            self.fields['container_select_option'].choices = \
                TransferInShelfObjectApproveWithContainerSerializer.TRANSFER_IN_CONTAINER_SELECT_CHOICES

        self.fields['available_container'] = forms.ModelChoiceField(
            queryset=ShelfObject.objects.none(),
            widget=AutocompleteSelect('available-container-search',
                                      attrs={
                                          'data-dropdownparent': modal_id,
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )
        self.fields['container_for_cloning'] = forms.ModelChoiceField(
            queryset=Object.objects.none(),
            widget=AutocompleteSelect('container-for-cloning-search',
                                      attrs={
                                          'data-dropdownparent': modal_id,
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )


class TransferInShelfObjectApproveWithContainerForm(ContainerForm):
    transfer_object = forms.IntegerField(widget=forms.HiddenInput)
    shelf = forms.IntegerField(widget=forms.HiddenInput)

class MoveShelfobjectWithContainerForm(ContainerForm, MoveShelfObjectForm):
    pass

class ShelfObjectReactiveForm(ShelfObjectExtraFields,ContainerForm,forms.ModelForm,GTForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)

        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch',
                                      attrs={
                                          'data-dropdownparent': "#reactive_form",
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization',
                                          'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
                                      }),
            label=_("Reactive"),
            help_text=_("Search by name, code or CAS number")
        )

        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('catalogunit',
                                      attrs={
                                          'data-dropdownparent': "#reactive_form",
                                          'data-s2filter-shelf': '#id_shelf',
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))


        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search',
                                      attrs={
                                          'data-dropdownparent': "#reactive_form",
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
                                      }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),
            label=_("Status")
        )

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity", "measurement_unit",
                  "container_select_option","container_for_cloning","available_container",
                  "description","marked_as_discard","batch","objecttype"]
        exclude =['laboratory_name','created_by', 'limit_quantity',"container", 'in_where_laboratory', 'shelf_object_url', 'shelf_object_qr','limits']
        widgets = {
            'shelf': forms.HiddenInput,
            'description': genwidgets.Textarea,
            'quantity': genwidgets.TextInput,

            'batch': genwidgets.TextInput,
            'marked_as_discard': genwidgets.CheckboxInput,
        }


class ShelfObjectRefuseReactiveForm(ShelfObjectExtraFields,ContainerForm,GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Reactive"),
            help_text=_("Search by name, code or CAS number")
        )
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('catalogunit', attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))

        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),
        label=_("Status"))

        self.fields['marked_as_discard'].initial=True


    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity", "measurement_unit",
                  "container_select_option","container_for_cloning","available_container",
                  "description","marked_as_discard","batch","objecttype"]
        exclude = ['created_by',"laboratory_name", "limit_quantity", 'limits',"container"]
        widgets = {
            'shelf': forms.HiddenInput,
            'limit_quantity': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'description': genwidgets.Textarea,
            'marked_as_discard': genwidgets.HiddenInput,
            'batch': genwidgets.TextInput

        }

class ContainerManagementForm(ContainerForm):
    shelf_object = forms.IntegerField(widget=forms.HiddenInput)
    shelf = forms.CharField(widget=genwidgets.HiddenInput)


class ShelfobjectMaintenanceForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org_pk')
        super(ShelfobjectMaintenanceForm, self).__init__(*args, **kwargs)
        self.fields["provider_of_maintenance"].queryset = Provider.objects.filter(laboratory__organization__pk=org)

    class Meta:
        model = ShelfObjectMaintenance
        fields = "__all__"

        widgets = {
            'maintenance_date': genwidgets.DateInput,
            'provider_of_maintenance': genwidgets.Select,
            'maintenance_observation': genwidgets.Textarea,
            'organization': genwidgets.HiddenInput,
            'validator': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }
class UpdateShelfobjectMaintenanceForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org_pk')
        super(UpdateShelfobjectMaintenanceForm, self).__init__(*args, **kwargs)
        self.fields["provider_of_maintenance"].queryset = Provider.objects.filter(laboratory__organization__pk=org)

    class Meta:
        model = ShelfObjectMaintenance
        fields = "__all__"

        widgets = {
            'maintenance_date': genwidgets.DateInput,
            'provider_of_maintenance': genwidgets.Select,
            'maintenance_observation': genwidgets.Textarea,
            'organization': genwidgets.HiddenInput,
            'validator': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject': genwidgets.HiddenInput,
        }

class ShelfobjectLogForm(GTForm, forms.ModelForm):


    class Meta:
        model = ShelfObjectLog
        fields = "__all__"

        widgets = {
            'description': genwidgets.Textarea,
            'organization': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }

class ShelfobjectCalibrateForm(GTForm, forms.ModelForm):

    field_order = ('calibrate_name', 'calibration_date', 'observation',
                   'organization', 'validator', 'created_by', "shelfobject")
    class Meta:
        model = ShelfObjectCalibrate
        fields = "__all__"


        widgets = {
            'calibrate_name': genwidgets.TextInput,
            'calibration_date': genwidgets.DateInput,
            'observation': genwidgets.Textarea,
            'organization': genwidgets.HiddenInput,
            'validator': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }


class UpdateShelfobjectCalibrateForm(GTForm, forms.ModelForm):


    field_order = ('calibrate_name', 'calibration_date', 'observation',
                   'organization', 'validator', 'created_by', "shelfobject")
    class Meta:
        model = ShelfObjectCalibrate
        fields = "__all__"

        widgets = {
            'calibrate_name': genwidgets.TextInput,
            'calibration_date': genwidgets.DateInput,
            'observation': genwidgets.Textarea,
            'organization': genwidgets.HiddenInput,
            'validator': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }

class ShelfObjectGuaranteeForm(GTForm, forms.ModelForm):


    class Meta:
        model = ShelfObjectGuarantee
        fields = "__all__"

        widgets = {
            'guarantee_initial_date': genwidgets.DateInput,
            'guarantee_final_date': genwidgets.DateInput,
            'contract': FileChunkedUpload,
            'organization': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }


class ShelfObjectTrainingForm(GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        id_form = kwargs.pop('id_form')
        super(ShelfObjectTrainingForm, self).__init__(*args, **kwargs)

        self.fields['intern_people_receive_training'] = forms.ModelChoiceField(
            queryset=Profile.objects.all(),
            label=_("Internal participants in training"),
            widget=AutocompleteSelectMultiple('org_profiles', attrs={
                'data-dropdownparent': id_form,
                'data-s2filter-organization': '#organization'
            }))

    class Meta:
        model = ShelfObjectTraining
        fields = "__all__"

        widgets = {
            'training_initial_date': genwidgets.DateInput,
            'training_final_date': genwidgets.DateInput,
            'number_of_hours': genwidgets.NumberInput,
            'intern_people_receive_training': genwidgets.SelectMultiple,
            'external_people_receive_training': genwidgets.Textarea,
            'observation': genwidgets.Textarea,
            'place': genwidgets.TextInput,
            'organization': genwidgets.HiddenInput,
            'created_by': genwidgets.HiddenInput,
            'shelfobject':genwidgets.HiddenInput,
        }

class EditEquimentShelfobjectForm(forms.ModelForm, GTForm):
    description = forms.CharField(widget=genwidgets.Textarea, label=_("Description"))
    status = forms.ModelChoiceField(queryset=Catalog.objects.filter(key='shelfobject_status'), label=_("Status"), widget=genwidgets.Select)
    marked_as_discard = forms.BooleanField(widget=genwidgets.YesNoInput, required=False, label=_("Mark as discard"))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop("org_pk")
        super(EditEquimentShelfobjectForm, self).__init__(*args, **kwargs)

        self.fields['provider'] = forms.ModelChoiceField(
            queryset=Provider.objects.all(),
            label= _("Provider"),
            widget=AutocompleteSelect('object_providers', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-object': '#id_object',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#organization'
            }))
        org= OrganizationStructure.objects.get(pk=org)
        self.fields['authorized_roles_to_use_equipment'].queryset= Rol.objects.filter(pk__in=org.rol.values_list('pk',flat=True))

    field_order = ["status", "marked_as_discard", "description", "provider",
                   "authorized_roles_to_use_equipment", "equipment_price",
                   "purchase_equipment_date", "delivery_equipment_date",
                   "have_guarantee", "contract_of_maintenance", "available_to_use",
                   "first_date_use", "notes"]
    class Meta:

        model = ShelfObjectEquipmentCharacteristics
        fields = "__all__"

        exclude = ["created_by"]
        widgets = {
            "organization": genwidgets.HiddenInput,
            "shelfobject": genwidgets.HiddenInput,
            "provider": genwidgets.Select,
            "authorized_roles_to_use_equipment": genwidgets.SelectMultiple,
            "equipment_price": genwidgets.TextInput,
            "purchase_equipment_date": genwidgets.DateInput,
            "delivery_equipment_date": genwidgets.DateInput,
            "have_guarantee": genwidgets.YesNoInput,
            "notes": genwidgets.Textarea,
            "contract_of_maintenance": FileChunkedUpload,
            "available_to_use":genwidgets.YesNoInput,
            "first_date_use":genwidgets.DateInput,
        }
