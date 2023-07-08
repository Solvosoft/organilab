from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple
from djgentelella.widgets.tagging import TaggingInput

from sga.models import Substance, RecipientSize, TemplateSGA, DangerIndication, DangerPrudence, DisplayLabel, \
    BuilderInformation, Label, SGAComplement, Provider


class PersonalTemplateForm(GTForm):
    name = forms.CharField(max_length=100, required=True, widget=genwidgets.TextInput, label=_('Name'))
    template = forms.ModelChoiceField(queryset=TemplateSGA.objects.none(), required=True, widget=genwidgets.Select,
                                      label=_('Template'))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PersonalTemplateForm, self).__init__(*args, **kwargs)
        filter = Q(community_share=True) | Q(created_by=user)
        self.fields['template'].queryset = TemplateSGA.objects.filter(filter)


class SGAEditorForm(forms.ModelForm, GTForm):
    class Meta:
        model = DangerPrudence
        fields = ('prudence_advice', 'danger_indication')
        exclude = ['']
        widgets = {
            'prudence_advice': AutocompleteSelect('prudencesearch'),
            'danger_indication': AutocompleteSelect('dangersearch')
        }


class PersonalEditorForm(forms.ModelForm, GTForm):
    recipient_size = forms.ModelChoiceField(queryset=RecipientSize.objects.using(settings.READONLY_DATABASE),
                                            widget=genwidgets.Select,
                                            label=_("Recipient size"))

    class Meta:
        model = DisplayLabel
        fields = ('name',  'json_representation', 'preview', 'recipient_size')
        widgets = {
            'name': genwidgets.TextInput,
            'preview': genwidgets.HiddenInput,
            'json_representation': genwidgets.HiddenInput
        }

class EditorForm(forms.ModelForm, GTForm):
    preview = forms.CharField(widget=forms.HiddenInput())
    json_representation = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = TemplateSGA
        fields = ('name', 'recipient_size', 'json_representation', 'community_share', 'preview')
        widgets = {
            'name': genwidgets.TextInput,
            'recipient_size': genwidgets.Select,
            'community_share': genwidgets.YesNoInput
        }


class SearchDangerIndicationForm(GTForm):
    codes = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all().exclude(code="Ninguno"),
                                           widget=genwidgets.SelectMultiple, required=True)


class PersonalForm(GTForm):
    name = forms.CharField(max_length=100, required=True, widget=genwidgets.TextInput)
    company_name = forms.CharField(max_length=150, required=True, widget=genwidgets.TextInput)
    address = forms.CharField(widget=genwidgets.Textarea)
    phone = forms.CharField(max_length=50, required=True, widget=genwidgets.TextInput)
    json_representation = forms.CharField(widget=forms.HiddenInput())
    preview = forms.CharField(widget=forms.HiddenInput())
    template = forms.ModelChoiceField(queryset=TemplateSGA.objects.none(), required=False,
                                      widget=genwidgets.HiddenInput)
    substance = forms.ModelChoiceField(queryset=Substance.objects.all(), widget=genwidgets.Select)
    commercial_information = forms.CharField(widget=genwidgets.Textarea)
    barcode = forms.CharField(widget=genwidgets.TextInput, max_length=150, required=False)
    logo = forms.FileField(widget=genwidgets.FileInput, required=False)
    logo_upload_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PersonalForm, self).__init__(*args, **kwargs)
        filter = Q(community_share=True) | Q(created_by=user)
        self.fields['template'].queryset = TemplateSGA.objects.filter(filter)
        self.fields['address'].widget.attrs['rows'] = 4
        self.fields['commercial_information'].widget.attrs['rows'] = 4


class PersonalFormAcademic(GTForm):
    name = forms.CharField(max_length=100, required=True, widget=genwidgets.TextInput)
    company_name = forms.CharField(max_length=150, required=True, widget=genwidgets.TextInput)
    address = forms.CharField(widget=genwidgets.Textarea)
    phone = forms.CharField(max_length=50, required=True, widget=genwidgets.TextInput)
    json_representation = forms.CharField(widget=forms.HiddenInput())
    preview = forms.CharField(widget=forms.HiddenInput())
    template = forms.ModelChoiceField(queryset=TemplateSGA.objects.none(), required=False,
                                      widget=genwidgets.HiddenInput)
    substance = forms.CharField(widget=forms.HiddenInput())
    commercial_information = forms.CharField(widget=genwidgets.Textarea)
    barcode = forms.CharField(widget=genwidgets.TextInput, max_length=150, required=False)
    logo = forms.FileField(widget=genwidgets.FileInput, required=False)
    logo_upload_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        substance = kwargs.pop('substance')
        super(PersonalFormAcademic, self).__init__(*args, **kwargs)
        filter = Q(community_share=True) | Q(created_by=user)
        self.fields['substance'].initial = substance
        self.fields['template'].queryset = TemplateSGA.objects.filter(filter)
        self.fields['address'].widget.attrs['rows'] = 4
        self.fields['commercial_information'].widget.attrs['rows'] = 4


class PersonalSGAForm(forms.ModelForm, GTForm):
    recipient_size = forms.ModelChoiceField(widget=genwidgets.Select, queryset=RecipientSize.objects.all(), required=True)

    class Meta:
        model = DisplayLabel
        fields = ['name', 'json_representation', 'preview', 'recipient_size']
        widgets = {
            'name': genwidgets.TextInput,
            'preview': genwidgets.HiddenInput,
            'json_representation': genwidgets.HiddenInput,
        }

class PersonalSGAAddForm(forms.ModelForm, GTForm):
    class Meta:
        model = DisplayLabel
        fields = ['logo', 'barcode']
        exclude = ['user']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'barcode': genwidgets.NumberInput
        }
class BuilderInformationForm(forms.ModelForm, GTForm):

    class Meta:
        model = BuilderInformation
        fields = ['name', 'address', 'phone', 'commercial_information']
        exclude = ['user', ]
        widgets ={
            'address': genwidgets.TextInput,
            'phone': genwidgets.TextInput,
            'name': genwidgets.TextInput,
            'commercial_information': genwidgets.Textarea
        }


class LabelForm(forms.ModelForm, GTForm):
    class Meta:
        model = Label
        fields = ['substance']
        exclude = ['builderInformation']
        widgets = {
            'substance': genwidgets.Select
        }


class PersonalTemplatesForm(GTForm):
    name = forms.CharField(max_length=100, required=True)
    json_data = forms.CharField(widget=forms.TextInput)


class SubstanceForm(forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        super(SubstanceForm, self).__init__(*args, **kwargs)
        self.fields['uipa_name'].label = _('UIPA name')

    class Meta:
        model = Substance
        fields = '__all__'
        widgets = {
            'comercial_name': genwidgets.TextInput,
            'uipa_name': genwidgets.TextInput,
            'components': genwidgets.SelectMultiple(),
            'danger_indications': genwidgets.SelectMultiple(),
            'synonymous': TaggingInput,
            'agrochemical': genwidgets.YesNoInput
        }


class RecipientSizeForm(forms.ModelForm, GTForm):
    class Meta:
        model = RecipientSize
        fields = '__all__'
        widgets = {
            'name': genwidgets.TextInput,
            'height': genwidgets.NumberInput,
            'height_unit': genwidgets.Select,
            'width': genwidgets.NumberInput,
            'width_unit': genwidgets.Select,

        }


class SGAComplementsForm(forms.ModelForm, GTForm):
    class Meta:
        model = SGAComplement
        fields = ('prudence_advice', 'danger_indication', 'warningword',   'other_dangers')
        order_fields = ('prudence_advice', 'danger_indication', 'warningword',  'other_dangers')
        widgets = {
            'prudence_advice': AutocompleteSelectMultiple('prudencesearch'),
            'danger_indication': AutocompleteSelectMultiple('dangersearch'),
            'warningword': genwidgets.Select,
            'substance': genwidgets.HiddenInput,
            'other_dangers': genwidgets.Textarea
        }

class ProviderSGAForm(forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        super(ProviderSGAForm, self).__init__(*args, **kwargs)
        self.fields['provider'].required = False
    field_order = ['name', 'country', 'provider', 'direction', 'telephone_number', 'fax', 'email', 'emergency_phone']

    class Meta:
        model = Provider
        fields = '__all__'
        widgets = {
            "name": genwidgets.TextInput(),
            "country": genwidgets.TextInput(),
            "direction": genwidgets.Textarea(),
            "telephone_number": genwidgets.TextInput(),
            "fax": genwidgets.TextInput(),
            "email": genwidgets.EmailInput(),
            "provider": genwidgets.Select(attrs={'data-dropdownparent': '#provider_modal',
                                             'data-placeholder': _('Select Provider')}),
            "emergency_phone": genwidgets.TextInput(),
        }


class SGALabelForm(forms.ModelForm, GTForm):
    class Meta:
        model = DisplayLabel
        fields = ['name', 'template']
        widgets = {
            "name": genwidgets.TextInput(),
            "template": genwidgets.Select(),
        }


class SGALabelComplementsForm(forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(SGALabelComplementsForm, self).__init__(*args, **kwargs)
        if org_pk:
            self.fields['substance'].queryset = Substance.objects.filter(organization__pk=org_pk)
        else:
            self.fields['substance'].queryset = Substance.objects.none()

    class Meta:
        model = SGAComplement
        fields = ('substance', 'prudence_advice', 'danger_indication', 'warningword',  'other_dangers')
        order_fields = ('substance', 'prudence_advice', 'danger_indication', 'warningword',  'other_dangers')
        widgets = {
            'prudence_advice': AutocompleteSelectMultiple('prudencesearch'),
            'danger_indication': AutocompleteSelectMultiple('dangersearch'),

            'warningword': genwidgets.Select,
            'substance': genwidgets.Select,
            'other_dangers': genwidgets.Textarea
        }


class SGALabelBuilderInformationForm(forms.ModelForm, GTForm):
    company = forms.ModelChoiceField(widget=genwidgets.Select(), queryset=BuilderInformation.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        user = None
        if 'user' in kwargs:
            user = kwargs.pop('user')
        super(SGALabelBuilderInformationForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['company'].queryset = BuilderInformation.objects.filter(user=user)


    field_order = ['company', 'name', 'address', 'phone', 'commercial_information']

    class Meta:
        model = BuilderInformation
        fields = ['name', 'address', 'phone', 'commercial_information']
        exclude = ['user', ]
        widgets ={
            'address': genwidgets.TextInput,
            'phone': genwidgets.TextInput,
            'name': genwidgets.TextInput,
            'commercial_information': genwidgets.Textarea
        }

class CompanyForm(forms.ModelForm, GTForm):
    def __init__(self, *args, **kwargs):
        user = None
        if 'user' in kwargs:
            user=kwargs.pop('user')
        super(CompanyForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['user'].initial = user

    class Meta:
        model = BuilderInformation
        exclude = ['created_by', 'organization']
        widgets = {
            'name': genwidgets.TextInput,
            'phone': genwidgets.TextInput,
            'address':genwidgets.Textarea,
            'commercial_information': genwidgets.Textarea,
            'user': genwidgets.HiddenInput

        }


class ValidateReviewSubstanceForm(forms.Form):
    showapprove = forms.BooleanField(required=False)
