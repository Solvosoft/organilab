from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from djgentelella.widgets.selects import AutocompleteSelectMultiple

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, Furniture, LaboratoryRoom, Object
from laboratory.utils import get_laboratories_from_organization, get_users_from_organization
from report.models import TaskReport, DocumentReportStatus


class ReportBase(GTForm):
    name = forms.CharField(max_length=100, label=_('File Name'), widget=genwidgets.TextInput(), required=True)
    title = forms.CharField(max_length=100, label=_('Report Title'), widget=genwidgets.TextInput(), required=True)
    organization = forms.IntegerField(widget=forms.HiddenInput())
    report_name = forms.CharField(widget=forms.HiddenInput())
    format = forms.ChoiceField(widget=genwidgets.Select, choices=(
        ('html', _('On screen')),
        ('pdf', _('PDF')),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
        ('ods', 'ODS')
    ), required=False, label=_('Format'))

    def clean_name(self):
        name = self.cleaned_data['name']
        name = slugify(name)
        return name


class ReportForm(ReportBase):
    all_labs_org = forms.BooleanField(help_text=_("This option allows to expand this query to all laboratories of current organization"),
        widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())

class ValidateReportForm(ReportBase):
    all_labs_org = forms.BooleanField(widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    laboratory = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Laboratory.objects.all())

    def clean_laboratory(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        laboratory = self.cleaned_data['laboratory']
        if all_labs_org:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list('pk',flat=True))

class ReportObjectsBaseForm(ReportBase):
    all_labs_org = forms.BooleanField(help_text=_("This option allows to expand this query to all laboratories of current organization"),
        widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    object_type = forms.CharField(max_length=1, widget=genwidgets.HiddenInput(), required=False)

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

class LaboratoryRoomReportForm(ReportBase):
    objects_type = list(Object.TYPE_CHOICES)
    objects_type.insert(0, (None, _("General")))
    all_labs_org = forms.BooleanField(help_text=_("This option allows to expand this query to all laboratories of current organization"),
        widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    laboratory = forms.ModelMultipleChoiceField(widget=forms.HiddenInput, queryset=Laboratory.objects.all())
    object_type = forms.ChoiceField(choices=tuple(objects_type), label=_("Object type"),
                                    required=False,
                                    widget=genwidgets.Select(attrs={'class': 'form-control'}))
    is_precursor = forms.BooleanField(widget=genwidgets.YesNoInput, required=False,
                                      label=_("Is precursor?"))
    lab_room = forms.ModelMultipleChoiceField(help_text=_("If you want to delimit this query select laboratory rooms (Optional)"),
        widget=AutocompleteSelectMultiple("lab_room", attrs={
        'data-related': 'true',
        'data-pos': 0,
        'data-groupname': 'labroomreport',
        'data-s2filter-organization': '#id_organization',
        'data-s2filter-laboratory': '#id_laboratory',
        'data-s2filter-all_labs_org': '#id_all_labs_org:checked'
    }),
    queryset=LaboratoryRoom.objects.all(), label=_('Filter Laboratory Room'), required=False)
    furniture = forms.ModelMultipleChoiceField(help_text=_("If you want to delimit this query select furnitures (Optional)"),
        widget=AutocompleteSelectMultiple("furniture", attrs={
        'data-related': 'true',
        'data-pos': 1,
        'data-groupname': 'labroomreport',
        'data-s2filter-organization': '#id_organization',
        'data-s2filter-laboratory': '#id_laboratory',
    }),
   queryset=Furniture.objects.all(), label=_('Filter Furniture'), required=False)


class ValidateLaboratoryRoomReportForm(ReportBase):
    all_labs_org = forms.BooleanField(widget=genwidgets.YesNoInput, required=False)
    laboratory = forms.ModelMultipleChoiceField(widget=forms.SelectMultiple, queryset=Laboratory.objects.all())
    lab_room = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=LaboratoryRoom.objects.all(), required=False)
    furniture = forms.ModelMultipleChoiceField(widget=genwidgets.SelectMultiple, queryset=Furniture.objects.all(), required=False)
    objects_type = list(Object.TYPE_CHOICES)
    objects_type.insert(0, (None, _("All")))
    object_type = forms.ChoiceField(choices=tuple(objects_type),
                                    required=False,
                                    widget=genwidgets.Select(
                                        attrs={'class': 'form-control'}))
    is_precursor = forms.BooleanField(widget=genwidgets.YesNoInput, required=False)
    def clean_laboratory(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        laboratory = self.cleaned_data['laboratory']

        if all_labs_org:
            laboratory = get_laboratories_from_organization(organization)

        return list(laboratory.values_list('pk',flat=True))

    def clean_lab_room(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        lab_room = self.cleaned_data['lab_room']
        laboratory = self.cleaned_data['laboratory']
        if all_labs_org:
            if not lab_room:
                laboratory = get_laboratories_from_organization(organization)
        else:
            if lab_room:
                lab_room = LaboratoryRoom.objects.filter(pk__in=lab_room)
            laboratory = Laboratory.objects.filter(pk__in=laboratory)

        if not lab_room:
            lab_room = LaboratoryRoom.objects.filter(laboratory__in=laboratory)
        return list(lab_room.values_list('pk',flat=True).distinct())


    def get_furniture(self, lab_room, laboratory):
        furniture = Furniture.objects.filter(labroom__laboratory__in=list(laboratory))
        if lab_room:
            furniture = furniture.filter(labroom__in=lab_room)
        furniture = furniture.distinct()
        return furniture

    def clean_furniture(self):
        organization = self.cleaned_data['organization']
        all_labs_org = self.cleaned_data['all_labs_org']
        lab_room = self.cleaned_data['lab_room']
        furniture = self.cleaned_data['furniture']
        laboratory = self.cleaned_data['laboratory']

        if not furniture:
            if all_labs_org:
                laboratory = get_laboratories_from_organization(organization)

                furniture = self.get_furniture(lab_room, laboratory)
            else:
                furniture = self.get_furniture(lab_room, laboratory)
        return list(furniture.values_list('pk',flat=True).distinct())

class ObjectLogChangeBaseForm(ReportBase):
    all_labs_org = forms.BooleanField(help_text=_("This option allows to expand this query to all laboratories of current organization"),
        widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    period = forms.CharField(widget=genwidgets.DateRangeInput, required=False,label=_('Period'))
    precursor = forms.BooleanField(widget=genwidgets.YesNoInput,  required=False,label=_('Precursor'))
    resume = forms.BooleanField(widget=genwidgets.YesNoInput, required=False,label=_('Resume'))

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
        return list(laboratory.values_list('pk',flat=True).distinct())

class OrganizationReactiveForm(ReportBase):
    users = forms.ModelMultipleChoiceField(help_text=_("If you want to delimit this query select users (Optional)"),
        widget=genwidgets.SelectMultiple(), queryset=Profile.objects.all(), label=_('Filter User'), required=False)

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(OrganizationReactiveForm, self).__init__(*args, **kwargs)

        if org_pk:
            self.fields['users'].queryset = Profile.objects.filter(user__in=get_users_from_organization(org_pk))

    def clean_user(self):
        organization = self.cleaned_data['organization']
        users = self.cleaned_data['users']

        if not users:
            users = get_users_from_organization(organization)

        return list(users.values_list('pk',flat=True))

    def clean_users(self):
        organization = self.cleaned_data['organization']
        users = self.cleaned_data['users']

        if not users:
            users = get_users_from_organization(organization)
        else:
            users = users.values_list('user__pk', flat=True)
        return list(users.distinct())

class ValidateObjectTypeForm(GTForm):
    type_id = forms.CharField(max_length=1)

    def clean_type_id(self):
        type_id = self.cleaned_data.get('type_id')
        if type_id:
            if not type_id in dict(Object.TYPE_CHOICES).keys():
                self.add_error('type_id', _("Object type is not allowed"))
            return type_id
        else:
            return None


class ValidateFurnitureForm(GTForm):
    furniture = forms.IntegerField()
    laboratory = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        laboratory = cleaned_data.get('laboratory')
        furniture = cleaned_data.get('furniture')

        if not furniture or not laboratory:
            self.add_error('furniture', _("Furniture is not allowed"))
        else:
            furniture_obj = Furniture.objects.filter(pk=furniture, labroom__laboratory=laboratory)
            if not furniture_obj.exists():
                self.add_error('furniture', _("Furniture is not allowed"))
        return cleaned_data

class TasksForm(GTForm):
    task = forms.CharField(max_length=255)
    taskreport = forms.IntegerField()

    def clean_taskreport(self):
        taskreport = self.cleaned_data.get('taskreport', 0)
        report = TaskReport.objects.filter(pk=taskreport)

        if not report.exists():
            self.add_error('taskreport', _("Task report doesn't exists"))
        return taskreport


class DiscardShelfForm(ReportBase):
    laboratory = forms.ModelChoiceField(widget=genwidgets.Select, queryset=Laboratory.objects.all())
    all_labs_organization = forms.BooleanField(help_text=_("This option allows to expand this query to all laboratories of current organization"),
        widget=genwidgets.YesNoInput, label=_("All laboratories"), required=False)
    period = forms.CharField(widget=genwidgets.DateRangeInput, required=False,label=_('Period'))

    def __init__(self, *args, **kwargs):
        org_pk = kwargs.pop('org_pk', None)
        super(DiscardShelfForm, self).__init__(*args, **kwargs)


        if org_pk:
            self.fields['laboratory'].queryset = Laboratory.objects.filter(organization=org_pk)

    def clean_laboratory(self):
        lab = self.cleaned_data.get('laboratory')
        if lab:
            return lab.id
        return lab
