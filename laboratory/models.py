from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from laboratory.validators import validate_molecular_formula


@python_2_unicode_compatible
class ObjectFeatures(models.Model):
    GENERAL_USE = "0"
    SECURITY_EQUIPMENT = "1"
    ANALYTIC_CHEMISTRY = "2"
    ORGANIC_CHEMISTRY = "3"
    PHYSICAL_CHEMISTRY = "4"
    CHEMICAL_BIOLOGICAL_PROCESS = "5"
    INDUSTRIAL_BIOTECHNOLOGY = "6"
    BIOCHEMISTRY = "7"
    WATER_CHEMISTRY = "8"
    OTHER = "9"
    CHOICES = (
        (GENERAL_USE, _('General use')),
        (SECURITY_EQUIPMENT, _('Security equipment')),
        (ANALYTIC_CHEMISTRY, _('Analytic Chemistry')),
        (ORGANIC_CHEMISTRY, _('Organic Chemistry')),
        (PHYSICAL_CHEMISTRY, _('Physical Chemistry')),
        (CHEMICAL_BIOLOGICAL_PROCESS, _('Chemical and Biological process')),
        (INDUSTRIAL_BIOTECHNOLOGY, _('Industrial Biotechnology')),
        (BIOCHEMISTRY, _('Biochemistry')),
        (WATER_CHEMISTRY, _('Water Chemistry')),
        (OTHER, _('Other'))
    )

    name = models.CharField(_('Name'), max_length=2, choices=CHOICES, unique=True)
    description = models.TextField(_('Description'))

    class Meta:
        verbose_name = _('Object feature')
        verbose_name_plural = _('Object features')

    def __str__(self):
        return '%s' % (self.CHOICES[int(self.name)][1],)


class Object(models.Model):
    REACTIVE = '0'
    MATERIAL = '1'
    EQUIPMENT = '2'
    TYPE_CHOICES = (
        (REACTIVE, _('Reactive')),
        (MATERIAL, _('Material')),
        (EQUIPMENT, _('Equipment'))
    )
    EXPLOSIVES = '1'
    GASES = '2'
    FLAMMABLE_LIQUIDS = '3'
    FLAMMABLE_SOLIDS = '4'
    OXIDIZING = '5'
    TOXIC = '6'
    RADIOACTIVE = '7'
    CORROSIVE = '8'
    MISCELLANEOUS = '9'
    IDMG_CHOICES = (
        (EXPLOSIVES, 'Explosives'),
        (GASES, 'Gases'),
        (FLAMMABLE_LIQUIDS, 'Flammable liquids'),
        (FLAMMABLE_SOLIDS, 'Flammable solids'),
        (OXIDIZING, 'Oxidizing substances and organic peroxides'),
        (TOXIC, 'Toxic and infectious substances'),
        (RADIOACTIVE, 'Radioactive material'),
        (CORROSIVE, 'Corrosive substances'),
        (MISCELLANEOUS, 'Miscellaneous dangerous substances and articles')
    )
    code = models.CharField(_('Code'), max_length=255)
    name = models.CharField(_('Name'), max_length=255)
    type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES)
    description = models.TextField(_('Description'))
    molecular_formula = models.CharField(_('Molecular formula'), max_length=255,
                                         validators=[validate_molecular_formula], null=True, blank=True)
    cas_id_number = models.CharField(
        _('Cas ID Number'), max_length=255, null=True, blank=True)
    security_sheet = models.FileField(
        _('Security sheet'), upload_to='security_sheets/', null=True, blank=True)
    is_precursor = models.BooleanField(_('Is precursor'), default=False)
    imdg_code = models.CharField(_("IMDG code"), choices=IDMG_CHOICES, max_length=1, null=True, blank=True)

    features = models.ManyToManyField(ObjectFeatures)

    class Meta:
        verbose_name = _('Object')
        verbose_name_plural = _('Objects')

    def __str__(self):
        return '%s %s' % (self.code, self.name,)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Object, self).save(*args, **kwargs)


class ShelfObject(models.Model):
    M = '0'
    MM = '1'
    CM = '2'
    L = '3'
    ML = '4'
    U = "5"
    CHOICES = (
        (M, _('Meters')),
        (MM, _('Milimeters')),
        (CM, _('Centimeters')),
        (L, _('Liters')),
        (ML, _('Mililiters')),
        (U, _('Unit'))
    )
    shelf = models.ForeignKey('Shelf')
    object = models.ForeignKey('Object')
    quantity = models.FloatField(_('Material quantity'))
    limit_quantity = models.FloatField(_('Limit material quantity'))
    measurement_unit = models.CharField(
        _('Measurement unit'), max_length=2, choices=CHOICES)

    @property
    def limit_reached(self):
        return self.quantity < self.limit_quantity

    class Meta:
        verbose_name = _('Shelf object')
        verbose_name_plural = _('Shelf objects')

    def __str__(self):
        return '%s - %s %s' % (self.object, self.quantity, self.CHOICES[int(self.measurement_unit)][1])


@python_2_unicode_compatible
class LaboratoryRoom(models.Model):
    name = models.CharField(_('Name'), max_length=255)

    class Meta:
        verbose_name = _('Laboratory Room')
        verbose_name_plural = _('Laboratory Rooms')

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Shelf(models.Model):
    CRATE = 'C'
    DRAWER = 'D'
    TYPE_CHOICES = (
        (CRATE, _('Space')),
        (DRAWER, _('Drawer'))
    )
    furniture = models.ForeignKey('Furniture')
    name = models.CharField(max_length=15, default="nd")
    container_shelf = models.ForeignKey('Shelf', null=True, blank=True)
    type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES)

    def get_objects(self):
        return ShelfObject.objects.filter(shelf=self)

    def count_objects(self):
        return ShelfObject.objects.filter(shelf=self).count()

    class Meta:
        verbose_name = _('Shelf')
        verbose_name_plural = _('Shelves')

    def __str__(self):
        return '%s %s %s' % (self.furniture, self.get_type_display(),
                             self.name)


@python_2_unicode_compatible
class Furniture(models.Model):
    FURNITURE = 'F'
    DRAWER = 'D'
    TYPE_CHOICES = (
        (FURNITURE, _('Furniture')),
        (DRAWER, _('Drawer'))
    )
    labroom = models.ForeignKey('LaboratoryRoom')
    name = models.CharField(_('Name'), max_length=255)
    type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES)
    dataconfig = models.TextField(_('Data configuration'))

    class Meta:
        verbose_name = _('Piece of furniture')
        verbose_name_plural = _('Furniture')
        ordering = ['name']

    def get_objects(self):
        return ShelfObject.objects.filter(shelf__furniture=self).order_by('shelf', '-shelf__name')

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Laboratory(models.Model):
    name = models.CharField(_('Laboratory name'), max_length=255)
    rooms = models.ManyToManyField(
        'LaboratoryRoom', blank=True)
    related_labs = models.ManyToManyField('Laboratory', blank=True)
    lab_admins = models.ManyToManyField(
        User, related_name='lab_admins', blank=True)
    laboratorists = models.ManyToManyField(
        User, related_name='laboratorists', blank=True)

    class Meta:
        verbose_name = _('Laboratory')
        verbose_name_plural = _('Laboratories')

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class FeedbackEntry(models.Model):
    title = models.CharField(_('Title'), max_length=255)
    explanation = models.TextField(_('Explanation'), blank=True)
    related_file = models.FileField(_('Related file'), upload_to='media/feedback_entries/', blank=True)

    class Meta:
        verbose_name = _('Feedback entry')
        verbose_name_plural = _('Feedback entries')

    def __str__(self):
        return '%s' % (self.title,)
