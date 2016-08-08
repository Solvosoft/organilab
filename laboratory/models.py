from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class LaboratoryRoom(models.Model):
    name = models.CharField('Name', max_length=255)

    class Meta:
        verbose_name = 'Laboratory Room'
        verbose_name_plural = 'Laboratory Rooms'

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Furniture(models.Model):
    FURNITURE = 'F'
    DRAWER = 'D'
    TYPE_CHOICES = (
        (FURNITURE, 'Furniture'),
        (DRAWER, 'Drawer')
    )
    labroom = models.ForeignKey('LaboratoryRoom')
    name = models.CharField('Name', max_length=255)
    type = models.CharField('Type', max_length=2, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = 'Piece of furniture'
        verbose_name_plural = 'Furniture'

    def __str__(self):
        return '%s' % (self.name,)


@python_2_unicode_compatible
class Shelf(models.Model):
    CRATE = 'C'
    DRAWER = 'D'
    TYPE_CHOICES = (
        (CRATE, 'Crate'),
        (DRAWER, 'Drawer')
    )
    furniture = models.ForeignKey('Furniture')
    container_shelf = models.ForeignKey('Shelf', null=True, blank=True)
    type = models.CharField('Type', max_length=2, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = 'Shelf'
        verbose_name_plural = 'Shelves'

    def __str__(self):
        return '%s' % (self.furniture,)

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
        (GENERAL_USE, 'General use'),
        (SECURITY_EQUIPMENT, 'Security equipment'),
        (ANALYTIC_CHEMISTRY, 'Analytic Chemistry'),
        (ORGANIC_CHEMISTRY, 'Organic Chemistry'),
        (PHYSICAL_CHEMISTRY, 'Physical Chemistry'),
        (CHEMICAL_BIOLOGICAL_PROCESS, 'Chemical and Biological process'),
        (INDUSTRIAL_BIOTECHNOLOGY, 'Industrial Biotechnology'),
        (BIOCHEMISTRY, 'Biochemistry'),
        (WATER_CHEMISTRY, 'Water Chemistry'),
        (OTHER, 'Other')
    )

    name = models.CharField('Name', max_length=2, choices=CHOICES)
    description = models.TextField('Description')

    class Meta:
        verbose_name = 'Object feature'
        verbose_name_plural = 'Object features'

    def __str__(self):
        return '%s' % self.CHOICES[int(self.name)][1]
