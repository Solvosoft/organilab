from django.forms import ModelForm
from djgentelella.forms.forms import GTForm
from django import forms
from djgentelella.widgets import core as genwidgets
from django.utils.translation import gettext_lazy as _
from djgentelella.widgets.selects import AutocompleteSelect

from laboratory import utils

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, Provider, Shelf, Catalog, ShelfObject, Object
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

class ShelfObjectExtraFields(GTForm,forms.Form):
    objecttype = forms.IntegerField(widget=genwidgets.HiddenInput, min_value=0, max_value=3, required=True)
    without_limit = forms.BooleanField(widget=genwidgets.CheckboxInput(attrs={'class':'check_limit'}), label=_('Unlimit'))
    minimum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Minimum Limit"))
    maximum_limit = forms.FloatField(widget=genwidgets.TextInput, required=True, initial=0.0, label=_("Maximum Limit"))
    expiration_date = forms.DateField(widget=genwidgets.DateInput,required=False, label=_("Expiration date"))


class ShelfObjectReactiveForm(ShelfObjectExtraFields,forms.ModelForm,GTForm):
    container = forms.ModelChoiceField(queryset=Object.objects.all(),required=True, label=_("Container"))

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)

        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
            attrs={
                'data-dropdownparent': "#reactive_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Reactive"),
            help_text=_("Search by name, code or CAS number")
        )
        self.fields['course_name'].label = _("Description")

        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#reactive_form",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Measurement unit"))

        self.fields['container'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('recipientsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
                                      attrs={
                                          'data-dropdownparent': "#reactive_form",
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#reactive_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),
        label=_("Status"))

    def clean_measurement_unit(self):
        unit = self.cleaned_data['measurement_unit']
        quantity = self.cleaned_data['quantity']
        shelf = self.cleaned_data['shelf']
        amount = quantity <= shelf.quantity and (quantity+shelf.get_total_refuse()) <= shelf.quantity
        if shelf.measurement_unit==None:
            return unit
        if shelf.measurement_unit==unit:
            if amount or shelf.quantity==0:
                return unit
            else:
                self.add_error('quantity', _("The quantity is more than the shelf has"))

        else:
            self.add_error('measurement_unit',
                           _("Need add the same measurement unit that the shelf has  %(measurement_unit)s")%{
                            'measurement_unit': shelf.measurement_unit
                        })

        return unit


    class Meta:
        model = ShelfObject
        fields = ["object","shelf","status","quantity", "measurement_unit","container", "course_name", "marked_as_discard", "batch", "objecttype"]
        exclude =['laboratory_name','creator', 'limit_quantity', 'in_where_laboratory', 'shelf_object_url', 'shelf_object_qr','limits']
        widgets = {
            'shelf': forms.HiddenInput,
            'course_name': genwidgets.Textarea,
            'quantity': genwidgets.TextInput,

            'batch': genwidgets.TextInput,
            'marked_as_discard': genwidgets.CheckboxInput,
        }

class ShelfObjectRefuseReactiveForm(ShelfObjectExtraFields,GTForm, forms.ModelForm):
    container = forms.ModelChoiceField(queryset=Object.objects.all(),required=True)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Reactive"),
            help_text=_("Search by name, code or CAS number")
        )
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#reactive_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
            }),
            label=_("Measurement unit"))
        self.fields['container'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('recipientsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
                                      attrs={
                                          'data-dropdownparent': "#reactive_refuse_form",
                                      }),
            label=_("Container"),
            help_text=_("Search by name")
        )
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#reactive_refuse_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),
        label=_("Status"))
        self.fields['course_name'].label = _("Description")
        self.fields['marked_as_discard'].initial=True


    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        shelf = cleaned_data.get("shelf")
        measurement_unit = cleaned_data.get("measurement_unit")

        if shelf.measurement_unit == measurement_unit or not shelf.measurement_unit:
            total = shelf.get_total_refuse()
            new_total =total+quantity
            if shelf.quantity>=new_total or not shelf.quantity:
                return cleaned_data
            else:
                self.add_error('quantity',_("The quantity is much larger than the shelf limit %(limit)s"%{
                    'limit': "%s"%(shelf.quantity,)}))
        else:
            self.add_error('measurement_unit',
                           _("The measurent unit is different of there shelf has %(measurement_unit)s")%{
                               'measurement_unit': shelf.measurement_unit
                           })
        return cleaned_data

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
class ShelfObjectMaterialForm(ShelfObjectExtraFields,forms.ModelForm,GTForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
            attrs={
                'data-dropdownparent': "#material_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label="Material")

        self.fields['course_name'].label = _("Description")
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#material_form",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#material_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0

    def clean_measurement_unit(self):
        unit = self.cleaned_data['measurement_unit']
        quantity = self.cleaned_data['quantity']
        shelf = self.cleaned_data['shelf']
        amount = quantity <= shelf.quantity and (quantity+shelf.get_total_refuse()) <= shelf.quantity
        if shelf.measurement_unit==None:
            return unit
        if shelf.measurement_unit==unit:
            if amount or shelf.quantity==0:
                return unit
            else:
                self.add_error('quantity', _("The quantity is more than the shelf has"))

        else:
            self.add_error('measurement_unit',
                           _("Need add the same measurement unit that the shelf has  %(measurement_unit)s")%{
                            'measurement_unit': shelf.measurement_unit
                        })

        return unit


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

class ShelfObjectRefuseMaterialForm(ShelfObjectExtraFields,GTForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)

        super().__init__(*args, **kwargs)
        self.fields['object'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label="Material")
        self.fields['course_name'].label = _("Description")

        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0
        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#material_refuse_form",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#material_refuse_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        shelf = cleaned_data.get("shelf")
        measurement_unit = cleaned_data.get("measurement_unit")

        if shelf.measurement_unit == measurement_unit or not shelf.measurement_unit:
            total = shelf.get_total_refuse()
            new_total =total+quantity
            if shelf.quantity>=new_total or not shelf.quantity:
                return cleaned_data
            else:
                self.add_error('quantity',_("The quantity is much larger than the shelf limit %(limit)s"%{
                    'limit': "%s"%(shelf.quantity,)}))
        else:
            self.add_error('measurement_unit',
                           _("The measurent unit is different of there shelf has %(measurement_unit)s")%{
                               'measurement_unit': shelf.measurement_unit
                           })
        return cleaned_data

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
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk},
            attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Equipment"))
        self.fields['course_name'].label = _("Description")

        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#equipment_form",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#equipment_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),label=_("Status"))
        self.fields['limit_quantity'].initial=0

    def clean_measurement_unit(self):
        unit = self.cleaned_data['measurement_unit']
        quantity = self.cleaned_data['quantity']
        shelf = self.cleaned_data['shelf']
        amount = quantity <= shelf.quantity and (quantity+shelf.get_total_refuse()) <= shelf.quantity
        if shelf.measurement_unit==None:
            return unit
        if shelf.measurement_unit==unit:
            if amount or shelf.quantity==0:
                return unit
            else:
                self.add_error('quantity', _("The quantity is more than the shelf has"))

        else:
            self.add_error('measurement_unit',
                           _("Need add the same measurement unit that the shelf has  %(measurement_unit)s")%{
                            'measurement_unit': shelf.measurement_unit
                        })

        return unit


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
            widget=AutocompleteSelect('objectorgsearch', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-shelf': '#id_shelf',
                'data-s2filter-objecttype': f'#id_{self.prefix}-objecttype'
            }),
            label=_("Equipment"))


        self.fields['measurement_unit'] = forms.ModelChoiceField(
            queryset=Object.objects.all(),
            widget=AutocompleteSelect('catalogunit', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#equipment_refuse_form",
                'data-s2filter-shelf': '#id_shelf'
            }),
            label=_("Measurement unit"))
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}, attrs={
                'data-dropdownparent': "#equipment_refuse_form",
            }),
            help_text='<a class="add_status float-end fw-bold">%s</a>'%(_("Click here to create a new status")),label=_("Status"))
        self.fields['marked_as_discard'].initial=True
        self.fields['limit_quantity'].initial=0

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        shelf = cleaned_data.get("shelf")
        measurement_unit = cleaned_data.get("measurement_unit")

        if shelf.measurement_unit == measurement_unit or not shelf.measurement_unit:
            total = shelf.get_total_refuse()
            new_total =total+quantity
            if shelf.quantity>=new_total or not shelf.quantity:
                return cleaned_data
            else:
                self.add_error('quantity',_("The quantity is much larger than the shelf limit %(limit)s"%{
                    'limit': "%s"%(shelf.quantity,)}))
        else:
            self.add_error('measurement_unit',
                           _("The measurent unit is different of there shelf has %(measurement_unit)s")%{
                               'measurement_unit': shelf.measurement_unit
                           })
        return cleaned_data

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
    description = forms.CharField(widget=genwidgets.Textarea)

    def __init__(self, *args, **kwargs):
        org_pk=kwargs.pop('org_pk')
        super().__init__(*args, **kwargs)
        self.fields['status'] = forms.ModelChoiceField(
            queryset=Catalog.objects.all(),
            widget=AutocompleteSelect('shelfobject_status_search', url_suffix='-detail', url_kwargs={'pk': org_pk}),
            help_text='<a class="add_status float-end fw-bold m-2"><i class="fa fa-plus"></i> %s</a>'%(_("New status")),label=_("Status"))


    class Meta:
        model = ShelfObject
        fields = ['status']
