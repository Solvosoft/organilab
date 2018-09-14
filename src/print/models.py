'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from location_field.models.plain import PlainLocationField


class Contact(models.Model):
    name = models.TextField(_('Name'), default='', max_length=255)
    phone = models.TextField(max_length=15, verbose_name=_("Phone"))

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


class Print(models.Model):
    responsible_user = models.ForeignKey(
        User, verbose_name=_("Responsible User"))
    email = models.EmailField(_('Email address'))
    location = models.TextField(_('Location'), default='', max_length=255)
    geolocation = PlainLocationField(zoom=15)
    name = models.TextField(_('Name'), default='', max_length=255)
    logo = models.ImageField(
        _('Logo'), upload_to='../media/print_logos', null=True, blank=True)
    qualification = models.IntegerField(
        _('Qualification'))
    creation_date = models.DateField(_('Creation Date'))
    state = models.TextField(_('State'), default='', max_length=255)
    # The several paper types can be on multiple printers and each print has multiple paper types
    paperType = models.ManyToManyField(
        PaperType, verbose_name=_("Paper Types"))
    # The several contact can be on multiple printers and each print has multiple contacts
    contacts = models.ManyToManyField(Contact, verbose_name=_("Contacts"))
    # Horary
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
    # Other important data
    description = models.TextField(
        _('Description'), default='', max_length=255)
    advertisement = models.TextField(
        _('Advertisement'), default='', max_length=255)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Print')
        verbose_name_plural = _('Printers')
