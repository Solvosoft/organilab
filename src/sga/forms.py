from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelect
from djgentelella.forms.forms import GTForm
from sga.models import Substance, RecipientSize, TemplateSGA, DangerIndication,DangerPrudence,PersonalTemplateSGA


class RecipientInformationForm(forms.Form):
    substance = forms.ModelChoiceField(queryset=Substance.objects.all())
    name = forms.CharField(max_length=150, required=True )
    phone = forms.CharField(max_length=15, required=True )
    address = forms.CharField(max_length=100, required=True )
    commercial_information = forms.Textarea( )
    templates = forms.ModelChoiceField(queryset=TemplateSGA.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(RecipientInformationForm, self).__init__(*args, **kwargs)
        filter = Q(community_share=True) | Q(creator=user)
        self.fields['templates'].queryset = TemplateSGA.objects.filter(filter)

class SGAEditorForm(CustomForm,forms.ModelForm):
    class Meta:
        model = DangerPrudence
        fields = ('prudence_advice','danger_indication')
        widgets = {
            'prudence_advice':AutocompleteSelect('prudencesearch'),
            'danger_indication': AutocompleteSelect('dangersearch')
        }

class EditorForm(forms.ModelForm):
    preview = forms.CharField(widget=forms.HiddenInput())
    json_representation = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = TemplateSGA
        fields = ('name', 'recipient_size', 'json_representation', 'community_share', 'preview')


class SearchDangerIndicationForm(CustomForm, forms.Form):

    codes = forms.ModelMultipleChoiceField(queryset=DangerIndication.objects.all().exclude(code="Ninguno"), widget=genwidgets.SelectMultiple, required=True)

class PersonalForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    json_representation = forms.CharField(widget=forms.HiddenInput()),
    sizes = forms.CharField(required=True, widget=genwidgets.NumberInput)

class DonateForm(GTForm, forms.Form):
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


class PersonalTemplatesForm(CustomForm, forms.Form):
    name = forms.CharField(max_length=100, required=True)
    json_data = forms.CharField(widget=forms.TextInput)

class SubstanceForm(GTForm,forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SubstanceForm, self).__init__(*args, **kwargs)
        self.fields['uipa_name'].label= _('UIPA name')
    class Meta:
        model = Substance
        fields= '__all__'
        widgets = {
            'comercial_name':genwidgets.TextInput,
            'uipa_name': genwidgets.TextInput,
            'components': genwidgets.SelectMultiple(),
            'danger_indications': genwidgets.SelectMultiple(),
            'synonymous': genwidgets.TextInput,
            'agrochemical': genwidgets.YesNoInput
        }

class RecipientSizeForm(GTForm,forms.ModelForm):

    class Meta:
        model = RecipientSize
        fields= '__all__'
        widgets = {
            'name':genwidgets.TextInput,
            'height': genwidgets.NumberInput,
            'height_unit': genwidgets.Select,
            'width': genwidgets.NumberInput,
            'width_unit': genwidgets.Select,

        }