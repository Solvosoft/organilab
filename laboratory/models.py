from __future__ import unicode_literals

import ast
import json

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from pyEQL import Solution as PySolution
from mptt.models import MPTTModel, TreeForeignKey
from location_field.models.plain import PlainLocationField
from laboratory.validators import validate_molecular_formula


@python_2_unicode_compatible
class CLInventory(models.Model):
    name = models.TextField(_('Name'))
    cas_id_number = models.TextField(_('CAS ID number'))
    url = models.TextField(_('URL'))

    class Meta:
        verbose_name = _('C&L Inventory')
        verbose_name_plural = _('C&L Inventory objects')
        permissions = (
            ("view_clinventory", _("Can see available C&L Inventory")),
        )

    def __str__(self):
        return '%s' % self.name


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

    name = models.CharField(_('Name'), max_length=2,
                            choices=CHOICES, unique=True)
    description = models.TextField(_('Description'))

    class Meta:
        verbose_name = _('Object feature')
        verbose_name_plural = _('Object features')
        permissions = (
            ("view_objectfeatures", _("Can see available objectfeatures")),
        )

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
    imdg_code = models.CharField(
        _("IMDG code"), choices=IDMG_CHOICES, max_length=1, null=True, blank=True)

    features = models.ManyToManyField(ObjectFeatures)

    @property
    def is_reactive(self):
        return self.type == self.REACTIVE

    class Meta:
        verbose_name = _('Object')
        verbose_name_plural = _('Objects')
        permissions = (
            ("view_object", _("Can see available object")),
        )

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

    @staticmethod
    def get_units(unit):
        choices = dict(ShelfObject.CHOICES)
        unit = str(unit)
        if unit in choices:
            return str(choices[unit])

        return ''

    @property
    def limit_reached(self):
        return self.quantity < self.limit_quantity

    class Meta:
        verbose_name = _('Shelf object')
        verbose_name_plural = _('Shelf objects')
        permissions = (
            ("view_shelfobjects", _("Can see available shelf objects")),
        )

    def __str__(self):
        return '%s - %s %s' % (self.object, self.quantity, self.CHOICES[int(self.measurement_unit)][1])


@python_2_unicode_compatible
class LaboratoryRoom(models.Model):
    name = models.CharField(_('Name'), max_length=255)

    class Meta:
        verbose_name = _('Laboratory Room')
        verbose_name_plural = _('Laboratory Rooms')
        permissions = (
            ("view_shelf", _("Can see available shelf")),
        )

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

    def positions(self):
        if hasattr(self, 'furniture'):
            furniture = self.furniture
            if furniture:
                return furniture.get_position_shelf(self.pk)
        return (None, None)

    def row(self):
        (row, col) = self.positions()
        return row

    def col(self):
        (row, col) = self.positions()
        return col

    class Meta:
        verbose_name = _('Shelf')
        verbose_name_plural = _('Shelves')
        permissions = (
            ("view_shelf", _("Can see available shelf")),
        )

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

    def remove_shelf_dataconfig(self, shelf_pk):
        if self.dataconfig:
            dataconfig = json.loads(self.dataconfig)

            for irow, row in enumerate(dataconfig):
                for icol, col in enumerate(row):
                    if col:
                        val = None
                        if type(col) == str:
                            val = col.split(",")
                        elif type(col) == int:
                            val = [col]
                            if shelf_pk in val:
                                val.set('')
                        elif type(col) == list:
                            val = col
                            if shelf_pk in val:
                                col.remove(shelf_pk)
                        else:
                            continue

                        if int(shelf_pk) in val:
                            val.remove(int(shelf_pk))

            self.dataconfig = str(dataconfig)
            self.save()

    def change_shelf_dataconfig(self, shelf_row, shelf_col, shelf_pk):
        if self.dataconfig:
            dataconfig = json.loads(self.dataconfig)

            for irow, row in enumerate(dataconfig):
                for icol, col in enumerate(row):
                    if col:
                        val = None
                        if type(col) == str:
                            val = col.split(",")
                        elif type(col) == int:
                            val = [col]
                        elif type(col) == list:
                            val = col
                        else:
                            continue
                        # remove old postion
                        if int(shelf_pk) in val:
                            val.remove(int(shelf_pk))

                        if shelf_row == irow and shelf_col == icol:
                            val.append(shelf_pk)

                    else:  # add id when it is white
                        if shelf_row == irow and shelf_col == icol:
                            col.append(shelf_pk)
            self.dataconfig = str(dataconfig)
            self.save()

    def get_position_shelf(self, shelf_pk):
        if self.dataconfig:
            dataconfig = json.loads(self.dataconfig)

            for irow, row in enumerate(dataconfig):
                for icol, col in enumerate(row):
                    if col:
                        val = None
                        if type(col) == str:
                            val = col.split(",")
                        elif type(col) == int:
                            val = [col]
                        elif type(col) == list:
                            val = col
                        else:
                            continue
                        if shelf_pk in (val):
                            return [irow, icol]

        return [None, None]

    def get_row_count(self):
        if self.dataconfig:
            dataconfig = json.loads(self.dataconfig)
            count = len(dataconfig)
            return count
        return 0

    def get_col_count(self):
        if self.dataconfig:
            dataconfig = json.loads(self.dataconfig)
            for irow, row in enumerate(dataconfig):
                count = len(row)
                return count
        return 0

    class Meta:
        verbose_name = _('Piece of furniture')
        verbose_name_plural = _('Furniture')
        ordering = ['name']
        permissions = (
            ("view_furniture", _("Can see available Furniture")),
        )

    def get_objects(self):
        return ShelfObject.objects.filter(shelf__furniture=self).order_by('shelf', '-shelf__name')

    def __str__(self):
        return '%s' % (self.name,)


class OrganizationStructureManager(models.Manager):

    def filter_user(self, user):
        organizations = OrganizationStructure.objects.filter(
            principaltechnician__credentials=user)

        orgs = None
        for org in organizations:
            if orgs is None:
                orgs = Q(pk__in=org.get_descendants(include_self=True))
            else:
                orgs |= Q(pk__in=org.get_descendants(include_self=True))

        if orgs is None:
            return OrganizationStructure.objects.none()
        else:
            return OrganizationStructure.objects.filter(orgs)

    def get_children(self, org_id):
        return OrganizationStructure.objects.filter(pk=org_id).get_descendants(include_self=True)


@python_2_unicode_compatible
class OrganizationStructure(MPTTModel):
    name = models.CharField(_('Name'), max_length=255)
    group = models.ForeignKey(
        Group, blank=True, null=True, on_delete=models.SET_NULL)

    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='children')

    os_manager = OrganizationStructureManager()

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        permissions = (
            ("view_organizationstructure", _(
                "Can see available OrganizationStructure")),
        )

    class MPTTMeta:
        order_insertion_by = ['name', ]

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return self.__str__()

    @property
    def laboratories(self):
        labs = ""
        for lab in Laboratory.objects.filter(organization=self):
            if labs:
                labs += " -- "
            labs += lab.name
        return labs


@python_2_unicode_compatible
class PrincipalTechnician(models.Model):
    credentials = models.ManyToManyField(User)
    name = models.CharField(_('Name'), max_length=255)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)
    id_card = models.CharField(_('ID Card'), max_length=100)
    email = models.EmailField(_('Email address'))

    organization = TreeForeignKey(OrganizationStructure, blank=True, null=True)
    assigned = models.ForeignKey(
        'Laboratory', blank=True, null=True, on_delete=models.SET_NULL)

    class MPTTMeta:
        order_insertion_by = ['name', ]

    class Meta:
        permissions = (
            ("view_principaltechnician", _("Can see available PrincipalTechnician")),
        )

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return self.__str__()


@python_2_unicode_compatible
class Laboratory(models.Model):
    name = models.CharField(_('Laboratory name'), default='', max_length=255)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)

    location = models.CharField(_('Location'), default='', max_length=255)
    geolocation = PlainLocationField(
        default='9.895804362670006,-84.1552734375', zoom=15)

    organization = TreeForeignKey(OrganizationStructure)

    rooms = models.ManyToManyField(
        'LaboratoryRoom', blank=True)

    laboratorists = models.ManyToManyField(
        User, related_name='laboratorists', blank=True)

    students = models.ManyToManyField(
        User, related_name='students', blank=True)

    class Meta:
        verbose_name = _('Laboratory')
        verbose_name_plural = _('Laboratories')
        permissions = (
            ("view_laboratory", _("Can see available laboratory")),
        )

    class MPTTMeta:
        order_insertion_by = ['name', ]

    def __str__(self):
        return '%s' % (self.name,)

    def __repr__(self):
        return self.__str__()


@python_2_unicode_compatible
class Solution(models.Model):
    name = models.CharField(_('Name'), default='', max_length=255)
    solutes = models.TextField(_('Solutes'))
    volume = models.CharField(_('Volumen'), max_length=100)
    temperature = models.CharField(
        _('Temperature'), default='25 degC', max_length=100)
    pressure = models.CharField(_('Pressure'), default='1 atm', max_length=100)
    pH = models.IntegerField(_('pH'), default=7)

    class Meta:
        verbose_name = _('Solution')
        verbose_name_plural = _('Solutions')
        permissions = (
            ("view_Solution", _("Can see available Solution")),
        )

    def __str__(self):
        return self.name

    @property
    def solute_list(self):
        return ast.literal_eval(self.solutes)

    @property
    def solution_object(self):
        return PySolution(
            solutes=self.solute_list,
            volume=self.volume,
            temperature=self.temperature,
            pressure=self.pressure,
            pH=self.pH
        )
