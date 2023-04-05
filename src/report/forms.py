from django.urls import reverse
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from django import forms
from django.utils.translation import gettext_lazy as _

from laboratory.models import Laboratory, Furniture, LaboratoryRoom
from laboratory.utils import get_laboratories_from_organization


class ReportBase(GTForm):
    name = forms.CharField(max_length=100, label=_('Name'), widget=genwidgets.TextInput(), required=True)
    title = forms.CharField(max_length=100, widget=genwidgets.TextInput(), required=True)
    organization = forms.IntegerField(widget=forms.HiddenInput())
    report_name = forms.CharField(widget=forms.HiddenInput())
    format = forms.ChoiceField(widget=genwidgets.Select, choices=(
        ('html', _('On screen')),
        ('pdf', _('PDF')),
        ('xls', 'XSL'),
        ('xlsx', 'XLSX'),
        ('ods', 'ODS')
    ), required=False, label=_('Format'))

    all_labs_org = forms.BooleanField(widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)

class ReportForm(ReportBase):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())


class ValidateReportForm(ReportBase):
    laboratory = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Laboratory.objects.all())

    def clean_laboratory(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        laboratory = self.cleaned_data['laboratory']
        if all_labs_org:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list('pk',flat=True))

class ReportObjectsBaseForm(ReportForm):
    name = forms.CharField(max_length=100, label=_('Name'), widget=genwidgets.TextInput(), required=True)
    title = forms.CharField(max_length=100, widget=genwidgets.TextInput(), required=True)
    organization = forms.IntegerField(widget=forms.HiddenInput())
    report_name = forms.CharField(widget=forms.HiddenInput())
    format = forms.ChoiceField(widget=genwidgets.Select, choices=(
        ('html', _('On screen')),
        ('pdf', _('PDF')),
        ('xls', 'XSL'),
        ('xlsx', 'XLSX'),
        ('ods', 'ODS')
    ), required=False, label=_('Format'))

    all_labs_org = forms.BooleanField(widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    object_type = forms.CharField(max_length=500, widget=genwidgets.HiddenInput())
    detail = forms.BooleanField(widget=genwidgets.YesNoInput(), required=False)

class ReportObjectsForm(ReportObjectsBaseForm):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())

class ReportObjectForm(ReportObjectsBaseForm):
    laboratory = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Laboratory.objects.all())

    def clean_laboratory(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        laboratory = self.cleaned_data['laboratory']

        if all_labs_org:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list('pk',flat=True))
    def clean_detail(self):
        detail = self.cleaned_data['detail']
        if detail:
            return detail
        else:
            return False

class RelOrganizationForm(GTForm):
    organization = forms.IntegerField()
    laboratory = forms.ModelMultipleChoiceField(queryset=Laboratory.objects.all())
    all_labs_org = forms.BooleanField(required=False)

class RelLaboratoryForm(GTForm):
    laboratory = forms.ModelMultipleChoiceField(queryset=Laboratory.objects.all())


class LaboratoryRoomReportForm(ReportBase):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())
    lab_room = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=LaboratoryRoom.objects.none(), label=_('Filter Laboratory Room'), required=False)
    furniture = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Furniture.objects.none(), label=_('Filter Furniture'), required=False)

    def __init__(self, *args, **kwargs):
        super(LaboratoryRoomReportForm, self).__init__(*args, **kwargs)
        self.fields['lab_room'].widget.attrs['data-url'] = reverse('labroombase-list')
        self.fields['furniture'].widget.attrs['data-url'] = reverse('furniturebase-list')


class ValidateLaboratoryRoomReportForm(ReportBase):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple, queryset=Laboratory.objects.all())
    lab_room = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=LaboratoryRoom.objects.all(), required=False)
    furniture = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Furniture.objects.all(), required=False)

class ObjectLogChangeBaseForm(GTForm):
    name = forms.CharField(max_length=100, label=_('Name'), widget=genwidgets.TextInput(), required=True)
    title = forms.CharField(max_length=100, widget=genwidgets.TextInput(), required=True)
    period = forms.CharField(widget=genwidgets.DateRangeInput, required=False,label=_('Period'))
    precursor = forms.BooleanField(widget=genwidgets.YesNoInput,  required=False,label=_('Precursor'))
    resume = forms.BooleanField(widget=genwidgets.YesNoInput, required=False,label=_('Resume'))
    report_name = forms.CharField(widget=forms.HiddenInput())
    all_labs_org = forms.BooleanField(widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    format = forms.ChoiceField(widget=genwidgets.Select,choices=(
        ('html', _('On screen')),
        ('pdf', _('PDF')),
        ('xls', 'XSL'),
        ('xlsx', 'XLSX'),
        ('ods', 'ODS')
    ), required=False,label=_('Format'))

    organization = forms.IntegerField(widget=genwidgets.HiddenInput)

class ObjectLogChangeReportForm(ObjectLogChangeBaseForm):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())

class ValidateObjectLogChangeReportForm(ObjectLogChangeBaseForm):
    laboratory = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple, queryset=Laboratory.objects.all())
    def clean_laboratory(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        laboratory = self.cleaned_data['laboratory']

        if all_labs_org:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list('pk',flat=True))