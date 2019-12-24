'''
Created by Luis Felipe Castro Sanchez
Universidad Nacional de Costa Rica 
Practica Profesional Supervisada (Julio - Noviembre 2018)
GitHub User luisfelipe7
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
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message=_(
        "Phone number must be entered in the format: '+55577777777'. Up to 15 digits allowed."))
    phone = models.CharField(
        validators=[phone_regex], max_length=15, blank=True, verbose_name=_("Phone"))  # validators should be a list
    assigned_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='Assigned_User')
    state = models.TextField(_('State'), default='Enabled', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')


# Reference to the creation of the Paper Type model: https://beatrizxe.com/es/blog/tipos-papel-impresion-mas-comunes.html
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
    grams = models.FloatField(_('Grams'))
    available = models.TextField(
        _('State'), default='Available', max_length=255)
    description = models.TextField(
        _('Description'), default='', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Paper Type')
        verbose_name_plural = _('Paper Types')


class Schedule(models.Model):
    name = models.TextField(_('Name'), default=_(
        'Normal Schedule'), max_length=255)
    DAYS = (
        ('Monday', _('Monday')),
        ('Tuesday', _('Tuesday')),
        ('Wednesday', _('Wednesday')),
        ('Thursday', _('Thursday')),
        ('Friday', _('Friday')),
        ('Saturday', _('Saturday')),
        ('Sunday', _('Sunday')),
    )
    startTime = models.TextField(_('Start Time'),  max_length=255)
    closeTime = models.TextField(_('Close Time'), max_length=255)
    startDay = models.CharField(
        max_length=50, default='Monday', verbose_name=_('Start Day'), choices=DAYS)
    closeDay = models.CharField(
        max_length=50, default='Friday', verbose_name=_('Close Day'), choices=DAYS)
    description = models.TextField(
        _('Schedule Description'), null=True, blank=True, max_length=255)
    state = models.TextField(_('State'), default='Enabled', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class Advertisement(models.Model):
    title = models.TextField(
        _('Title'), default='Advertisement', max_length=255)
    description = models.TextField(
        _('Advertisement Description'), max_length=255)
    typeOfAdvertisement = models.TextField(
        _('Type of advertisement'), default='Information', max_length=255)
    published_date = models.DateField(_('Published Date'), auto_now=True)
    state = models.TextField(_('State'), default='Enabled', max_length=100)
    usersNotified = models.ManyToManyField(
        User, verbose_name=_("Users Notified"))
    creator = models.ForeignKey(  # Fixed: Create a model for the advertisement
        User, on_delete=models.CASCADE, related_name='Creator', null=True, blank=True)

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
    advertisements = models.ManyToManyField(
        Advertisement, verbose_name=_("Advertisements"))

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Print')
        verbose_name_plural = _('Printers')
        permissions = (
            ("changeInformation_printObject", _(
                "Can edit the print information")),
            ("changeContacts_printObject", _(
                "Can edit the print contacts")),
            ("changePaper_printObject", _(
                "Can edit the print paper types")),
            ("changeSchedules_printObject", _(
                "Can edit the print schedules")),
            ("changeAdvertisements_printObject", _(
                "Can edit the print advertisements")),
        )

# DJANGO REST FRAMEWORK


class RequestLabelPrint(models.Model):
    STATUS_CHOICES = (
        (0, 'Requested'),
        (1, 'Preparing'),
        (2, 'Done'),
        (3, 'Rejected'),
        (4, 'Delivered'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    printer = models.ForeignKey(PrintObject, on_delete=models.CASCADE)
    add_date = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(default=0, choices=STATUS_CHOICES)

    def __str__(self):
        return str(self.user) + " -- " + str(self.print)
