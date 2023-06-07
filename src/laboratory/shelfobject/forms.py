from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple

from auth_and_perms.models import Profile
from laboratory import utils
from laboratory.models import Laboratory, Provider, Shelf, Catalog, ShelfObject, Object, LaboratoryRoom, Furniture
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
    amount = forms.FloatField(widget=genwidgets.TextInput, help_text=_('Use dot like 0.344 on decimal'), label=_('Amount'))
    bill = forms.CharField(widget=genwidgets.TextInput, label=_("Bill"), required=False)
    provider = forms.ModelChoiceField(queryset=Provider.objects.all(), label=_("Provider"), required=False,
                                      widget=AutocompleteSelect("provider", attrs={
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization',
                                      })
                                      )

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
        profile = Profile.objects.filter(pk=users.profile.pk).first()
        orgs = utils.get_pk_org_ancestors_decendants(users, org)

        self.fields['laboratory'].queryset = profile.laboratories.filter(organization__in=orgs).exclude(pk=lab)

class DecreaseShelfObjectForm(GTForm):
    amount = forms.DecimalField(widget=genwidgets.TextInput, help_text=_('Use dot like 0.344 on decimal'),
                                label=_('Amount'))
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
                                       'data-s2filter-shelf': '#id_shelf',
                                       'data-s2filter-organization': '#id_organization',
                                       'data-s2filter-laboratory': '#id_laboratory'
                                   }), help_text=_("This select only shows shelves with same measurement unit than current object")
                                   )

class ShelfObjectExtraFields(GTForm, forms.Form):
    objecttype = forms.IntegerField(widget=genwidgets.HiddenInput, min_value=0, max_value=3, required=True)
    without_limit = forms.BooleanField(widget=genwidgets.CheckboxInput(attrs={'class': 'check_limit'}),
                                       label=_('Unlimited'), initial=True)
    minimum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Minimum Limit"))
    maximum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Maximum Limit"))
    expiration_date = forms.DateField(widget=genwidgets.DateInput, required=False, label=_("Expiration date"))


class ShelfObjectReactiveForm(ShelfObjectExtraFields,forms.ModelForm,GTForm):    
    # TODO - this form needs to be updated to support also create a new container from an object and not only select it from the available shelfobjects in the lab
    
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

        self.fields['course_name'].label = _("Description")

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

        self.fields['container'] = forms.ModelChoiceField(
            queryset=ShelfObject.objects.none(),
            widget=AutocompleteSelect('available-container-search',
                                      attrs={
                                          'data-dropdownparent': "#reactive_form",
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )
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
        fields = ["object","shelf","status","quantity", "measurement_unit", "container", "course_name", "marked_as_discard", "batch", "objecttype"]
        exclude =['laboratory_name','creator', 'limit_quantity', 'in_where_laboratory', 'shelf_object_url', 'shelf_object_qr','limits']
        widgets = {
            'shelf': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
            'quantity': genwidgets.TextInput,

            'batch': genwidgets.TextInput,
            'marked_as_discard': genwidgets.CheckboxInput,
        }

class ShelfObjectRefuseReactiveForm(ShelfObjectExtraFields,GTForm, forms.ModelForm):
    # TODO - this form needs to be updated to support also create a new container from an object and not only select it from the available shelfobjects in the lab

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
        self.fields['container'] = forms.ModelChoiceField(
            queryset=ShelfObject.objects.none(),
            widget=AutocompleteSelect('available-container-search',
                                      attrs={
                                          'data-dropdownparent': "#reactive_refuse_form",
                                          'data-s2filter-laboratory': '#id_laboratory',
                                          'data-s2filter-organization': '#id_organization'
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),
        label=_("Status"))
        self.fields['course_name'].label = _("Description")
        self.fields['marked_as_discard'].initial=True


    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity", "measurement_unit","container","course_name","marked_as_discard","batch","objecttype"]
        exclude = ['creator',"laboratory_name", "limit_quantity", 'limits']
        widgets = {
            'shelf': forms.HiddenInput,
            'limit_quantity': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'course_name': genwidgets.Textarea,
            'marked_as_discard': genwidgets.HiddenInput,
            'batch': genwidgets.TextInput

        }

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

        self.fields['course_name'].label = _("Description")
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', attrs={
                'data-dropdownparent': "#material_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))
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
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
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
        self.fields['course_name'].label = _("Description")

        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0
    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
            'marked_as_discard': forms.HiddenInput
        }

class ShelfObjectEquimentForm(ShelfObjectExtraFields,forms.ModelForm,GTForm):

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
        self.fields['course_name'].label = _("Description")

        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("New status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0

    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity","limit_quantity","measurement_unit","marked_as_discard","course_name"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
            'marked_as_discard': genwidgets.CheckboxInput
        }

class ShelfObjectRefuseEquimentForm(ShelfObjectExtraFields,GTForm, forms.ModelForm):
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


        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-laboratory': '#id_laboratory',
                'data-s2filter-organization': '#id_organization'
            }),
            label=_("Measurement unit"))
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

    class Meta:
        model = ShelfObject
        fields = ["object", "shelf", "status", "quantity", "limit_quantity", "measurement_unit", "marked_as_discard",
                  "course_name"]
        widgets = {
            'shelf': forms.HiddenInput,
            'quantity': genwidgets.TextInput,
            'limit_quantity': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
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

