from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect, AutocompleteSelectMultiple
from djgentelella.widgets.tagging import TaggingInput

from sga.models import Substance, RecipientSize, TemplateSGA, DangerIndication, DangerPrudence, PersonalTemplateSGA, \
    BuilderInformation, Label, SGAComplement, Provider, Pictogram


class PersonalTemplateForm(GTForm):
    name = forms.CharField(max_length=100, required=True, widget=genwidgets.TextInput, label=_('Name'))
    template = forms.ModelChoiceField(queryset=TemplateSGA.objects.none(), required=True, widget=genwidgets.Select,
                                      label=_('Template'))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PersonalTemplateForm, self).__init__(*args, **kwargs)
        filter = Q(community_share=True) | Q(creator=user)
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
        filter = Q(community_share=True) | Q(creator=user)
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
        filter = Q(community_share=True) | Q(creator=user)
        self.fields['substance'].initial = substance
        self.fields['template'].queryset = TemplateSGA.objects.filter(filter)
        self.fields['address'].widget.attrs['rows'] = 4
        self.fields['commercial_information'].widget.attrs['rows'] = 4

class PersonalSGAForm(forms.ModelForm, GTForm):
    logo_upload_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = PersonalTemplateSGA
        fields = ['name', 'logo', 'barcode', 'template', 'logo_upload_id', 'json_representation', 'preview']
        exclude = ['user']
        widgets = {
            'logo': genwidgets.FileInput,
            'template': genwidgets.HiddenInput
        }


class BuilderInformationForm(forms.ModelForm, GTForm):
    class Meta:
        model = BuilderInformation
        fields = ['address', 'phone', 'name']
        exclude = ['user', 'community_share']


class LabelForm(forms.ModelForm, GTForm):
    class Meta:
        model = Label
        fields = ['substance']
        exclude = ['builderInformation']
        widgets = {
            'substance': genwidgets.Select
        }


class DonateForm(GTForm):
    name = forms.CharField(
        label=_('Name'), max_length=200, required=True,
        widget=genwidgets.TextInput)
    amount = forms.CharField(
        label=_('Amount'), required=True, widget=genwidgets.NumberInput,
        help_text=_("*Type the amount in dollars"))
    email = forms.CharField(
        label=_('Email'), required=True, widget=genwidgets.EmailMaskInput)
    is_donator = forms.BooleanField(
        label=_('Add me to the donators list'), widget=genwidgets.YesNoInput,
        initial=True)


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
        fields = ('prudence_advice', 'danger_indication', 'warningword', 'pictograms', 'other_dangers')
        order_fields = ('prudence_advice', 'danger_indication', 'warningword', 'pictograms', 'other_dangers')
        widgets = {
            'prudence_advice': AutocompleteSelectMultiple('prudencesearch'),
            'danger_indication': AutocompleteSelectMultiple('dangersearch'),
            'pictograms': genwidgets.SelectMultiple,
            'warningword': genwidgets.Select,
            'substance': genwidgets.HiddenInput,
            'other_dangers': genwidgets.Textarea
        }

class ProviderSGAForm(forms.ModelForm, GTForm):

    def __init__(self, *args, **kwargs):
        super(ProviderSGAForm, self).__init__(*args, **kwargs)
        self.fields['provider'].required = False

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


class PictogramForm(forms.ModelForm, GTForm):
    image_upload = forms.CharField(max_length=100, widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(PictogramForm, self).__init__(*args, **kwargs)
        self.fields['warning_word'].required = False

    class Meta:
        model = Pictogram
        fields = '__all__'
        exclude = ['id_pictogram']
        widgets = {
            "name": genwidgets.TextInput(),
            "warning_word": genwidgets.Select(),
            "image": genwidgets.FileInput(),
        }

class SGALabelForm(forms.ModelForm, GTForm):
    class Meta:
        model = PersonalTemplateSGA
        fields = ['name', 'template']
        widgets = {
            "name": genwidgets.TextInput(),
            "template": genwidgets.Select(),
        }


class SGALabelComplementsForm(forms.ModelForm, GTForm):
    class Meta:
        model = SGAComplement
        fields = ('substance', 'prudence_advice', 'danger_indication', 'warningword', 'pictograms', 'other_dangers')
        order_fields = ('substance', 'prudence_advice', 'danger_indication', 'warningword', 'pictograms', 'other_dangers')
        widgets = {
            'prudence_advice': AutocompleteSelectMultiple('prudencesearch'),
            'danger_indication': AutocompleteSelectMultiple('dangersearch'),
            'pictograms': genwidgets.SelectMultiple,
            'warningword': genwidgets.Select,
            'substance': genwidgets.Select,
            'other_dangers': genwidgets.Textarea
        }