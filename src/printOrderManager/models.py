'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from location_field.models.plain import PlainLocationField
# Import for the validators
from .validators import validate_email
from django.core.validators import RegexValidator
from django.core.validators import FileExtensionValidator


class Contact(models.Model):     # Fixed: Use user for the contacts
    phone = models.TextField(max_length=15, verbose_name=_("Phone"))
    assigned_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='Assigned_User')

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')


class PaperType(models.Model):
    UNITS = (
        ('mm', _('Milimeters')),
        ('cm', _('Centimeters')),
        ('inch', _('inch')),
    )
    unit_size = models.CharField(max_length=5, default='mm',
                                 verbose_name=_('Unit Size'),
                                 choices=UNITS)
    widthSize = models.FloatField(_('Width Size'))
    longSize = models.FloatField(_('Long Size'))
    name = models.TextField(_('Name'), default='', max_length=255)
    description = models.TextField(
        _('Description'), default='', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Paper Type')
        verbose_name_plural = _('Paper Types')


class Schedule(models.Model):
    DAYS = (
        ('mon', _('Monday')),
        ('tue', _('Tuesday')),
        ('wed', _('Wednesday')),
        ('thu', _('Thursday')),
        ('fri', _('Friday')),
        ('sat', _('Saturday')),
        ('sun', _('Sunday')),
    )
    startTime = models.TimeField(_("Start Time"))
    closeTime = models.TimeField(_("Close Time"))
    startDay = models.CharField(
        max_length=25, default='mon', verbose_name=_('Start Day'), choices=DAYS)
    closeDay = models.CharField(
        max_length=25, default='fri', verbose_name=_('Close Day'), choices=DAYS)
    description = models.TextField(
        _('Schedule Description'), default='Normal Schedule', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class Advertisement(models.Model):
    description = models.TextField(
        _('Advertisement Description'), max_length=255)
    published_date = models.DateField(_('Published Date'), auto_now=True)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')


class PrintObject(models.Model):
    responsible_user = models.ForeignKey(
        User, verbose_name=_("Responsible User"))
    email = models.EmailField(_('Email address'), validators=[validate_email])
    # The internationally standardized format E.164 : https://www.itu.int/rec/T-REC-E.164/es
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message=_(
        "Phone number must be entered in the format: '+55577777777'. Up to 15 digits allowed."))
    phone = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, verbose_name=_("Phone"))  # validators should be a list
    location = models.TextField(_('Location'), default='', max_length=255)
    geolocation = PlainLocationField(zoom=15)
    name = models.TextField(_('Name'), default='', max_length=255)
    logo = models.ImageField(
        _('Logo'), upload_to='print_logos/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'gif'])])  # Fixed : Create the folder media and the print_logos folder
    qualifications = (  # Fixed : SmallIntegerField and Choices
        (1, _('Very Bad')),
        (2, _('Bad')),
        (3, _('Good')),
        (4, _('Very Good')),
        (5, _('Excelent')),
    )
    qualification = models.SmallIntegerField(
        _('Qualification'), choices=qualifications)
    creation_date = models.DateField(
        _('Creation Date'), auto_now=True)  # Fixed: Auto_Now
    state = models.TextField(_('State'), default='', max_length=255)
    # The several paper types can be on multiple printers and each print has multiple paper types
    paperType = models.ManyToManyField(
        PaperType, verbose_name=_("Paper Types"))
    # The several contact can be on multiple printers and each print has multiple contacts
    contacts = models.ManyToManyField(Contact, verbose_name=_("Contacts"))
    # The several horary can be on multiple print and each print has multiple horary
    schedules = models.ManyToManyField(Schedule, verbose_name=_(
        "Schedules"))  # Fixed: Create a model for the schedules
    description = models.TextField(
        _('Description'), default='', max_length=255)
    # Print model has an advertisement
    advertisement = models.ForeignKey(  # Fixed: Create a model for the advertisement
        Advertisement, on_delete=models.CASCADE,  related_name='advertisements',null=True, blank=True)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Print')
        verbose_name_plural = _('Printers')
