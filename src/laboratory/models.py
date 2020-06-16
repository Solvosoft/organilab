import ast
import json

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from location_field.models.plain import PlainLocationField
from laboratory.validators import validate_molecular_formula
from . import catalog


class CLInventory(models.Model):
    name = models.TextField(_('Name'))
    cas_id_number = models.TextField(_('CAS ID number'))
    url = models.TextField(_('URL'))

    class Meta:
        verbose_name = _('C&L Inventory')
        verbose_name_plural = _('C&L Inventory objects')

    def __str__(self):
        return '%s' % self.name

class Catalog(models.Model):
    key = models.CharField(max_length=150)
    description = models.CharField(max_length=500)

    def __str__(self):
        return self.description

class ObjectFeatures(models.Model):
    name = models.CharField(_('Name'), max_length=250,  unique=True)
    description = models.TextField(_('Description'))

    class Meta:
        verbose_name = _('Object feature')
        verbose_name_plural = _('Object features')

    def __str__(self):
        return self.name

class Object(models.Model):
    REACTIVE = '0'
    MATERIAL = '1'
    EQUIPMENT = '2'
    TYPE_CHOICES = (
        (REACTIVE, _('Reactive')),
        (MATERIAL, _('Material')),
        (EQUIPMENT, _('Equipment'))
    )

    code = models.CharField(_('Code'), max_length=255)
    name = models.CharField(_('Name'), max_length=255)
    synonym = models.CharField(_('Synonym'), max_length=255, help_text=_('Comma separed name'), null=True, blank=True)
    type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES)
    is_public = models.BooleanField(default=True, verbose_name=_('Share with others'))
    description = models.TextField(_('Description'), null=True, blank=True)

    features = models.ManyToManyField(ObjectFeatures, verbose_name=_("Object features"))

    model = models.CharField(_('Model'), max_length=50, null=True, blank=True)
    serie = models.CharField(_('Serie'),  max_length=50, null=True, blank=True)
    plaque = models.CharField(
        _('Plaque'), max_length=50, null=True, blank=True)

    laboratory = models.ManyToManyField('Laboratory', blank=True)

    @property
    def is_reactive(self):
        return self.type == self.REACTIVE

    @property
    def is_precursor(self):
        if hasattr(self, 'sustancecharacteristics') and self.sustancecharacteristics:
            return self.sustancecharacteristics.is_precursor
        return False


    class Meta:
        verbose_name = _('Object')
        verbose_name_plural = _('Objects')


    def __str__(self):
        return '%s %s' % (self.code, self.name,)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Object, self).save(*args, **kwargs)

class SustanceCharacteristics(models.Model):
    obj = models.OneToOneField(Object, on_delete=models.CASCADE)
    iarc = catalog.GTForeignKey(Catalog, related_name="gt_iarcrel", on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IARC")
    imdg = catalog.GTForeignKey(Catalog, related_name="gt_imdg", on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IDMG")
    white_organ = catalog.GTManyToManyField(Catalog, related_name="gt_white_organ", key_name="key", key_value="white_organ")
    bioaccumulable = models.NullBooleanField(default=False)
    molecular_formula = models.CharField(_('Molecular formula'), max_length=255,
                                         validators=[validate_molecular_formula], null=True, blank=True)
    cas_id_number = models.CharField(
        _('Cas ID Number'), max_length=255, null=True, blank=True)
    security_sheet = models.FileField(
        _('Security sheet'), upload_to='security_sheets/', null=True, blank=True)
    is_precursor = models.BooleanField(_('Is precursor'), default=False)
    precursor_type = catalog.GTForeignKey(Catalog, related_name="gt_precursor", on_delete=models.SET_NULL,
                                null=True, blank=True, key_name="key", key_value="Precursor")

    h_code = models.ManyToManyField('sga.DangerIndication', verbose_name=_("Danger Indication"), blank=True)

    class Meta:
        verbose_name = _('Sustance characteristic')
        verbose_name_plural = _('Sustance characteristics')


class ShelfObject(models.Model):
    shelf = models.ForeignKey('Shelf', verbose_name=_("Shelf"), on_delete=models.CASCADE)
    object = models.ForeignKey('Object', verbose_name=_(
        "Equipment or reactive or sustance"), on_delete=models.CASCADE)
    quantity = models.FloatField(_('Material quantity'))
    limit_quantity = models.FloatField(_('Limit material quantity'))
    measurement_unit = catalog.GTForeignKey(Catalog, related_name="measurementunit", on_delete=models.DO_NOTHING,
                             verbose_name=_('Measurement unit'), key_name="key", key_value='units')


    @staticmethod
    def get_units(unit):
        if isinstance(unit, (int, str)):
            unit = Catalog.objects.filter(pk=unit).first() or ''
        return str(unit)
    @property
    def limit_reached(self):
        return self.quantity < self.limit_quantity


    def get_measurement_unit_display(self):
        return str(self.measurement_unit)


    class Meta:
        verbose_name = _('Shelf object')
        verbose_name_plural = _('Shelf objects')


    def __str__(self):
        return '%s - %s %s' % (self.object, self.quantity, str(self.measurement_unit))



class LaboratoryRoom(models.Model):
    name = models.CharField(_('Name'), max_length=255)

    class Meta:
        verbose_name = _('Laboratory Room')
        verbose_name_plural = _('Laboratory Rooms')

    def __str__(self):
        return '%s' % (self.name,)



class Shelf(models.Model):
    furniture = models.ForeignKey('Furniture', verbose_name=_("Furniture"), on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=15, default="nd")
    container_shelf = models.ForeignKey('Shelf', null=True, blank=True,
                                        verbose_name=_("Container shelf"), on_delete=models.CASCADE)

    # C space  D drawer
    type = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING,  verbose_name=_('Type'),
                                key_name="key", key_value='container_type')


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

    def __str__(self):
        return '%s %s %s' % (self.furniture, str(self.type), self.name)



class Furniture(models.Model):
    labroom = models.ForeignKey('LaboratoryRoom', on_delete=models.CASCADE)
    name = models.CharField(_('Name'), max_length=255)
    # old  'F' Cajón   'D' Estante
    type = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING,  verbose_name=_('Type'),
                                key_name="key", key_value='furniture_type')

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

    def get_objects(self):
        return ShelfObject.objects.filter(shelf__furniture=self).order_by('shelf', '-shelf__name')

    def __str__(self):
        return '%s' % (self.name,)


class OrganizationStructureManager(models.Manager):

    def filter_user(self, user):
        organizations = OrganizationStructure.objects.filter(
            organizationusermanagement__users=user)

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



class OrganizationStructure(MPTTModel):
    name = models.CharField(_('Name'), max_length=255)

    parent = TreeForeignKey(
        'self', blank=True, null=True, verbose_name=_("Parent"),
        related_name='children', on_delete=models.CASCADE)

    os_manager = OrganizationStructureManager()

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')

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


class OrganizationUserManagement(models.Model):
    group = models.ForeignKey(
        Group, blank=True, null=True, verbose_name=_("Group"),
        on_delete=models.SET_NULL)
    organization = models.ForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE)
    users = models.ManyToManyField(User, blank=True)

    class MPTTMeta:
        order_insertion_by = ['organization__name', ]

    def __str__(self):
        return "%s" % self.organization.name


class Laboratory(models.Model):
    name = models.CharField(_('Laboratory name'), default='', max_length=255)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)

    location = models.CharField(_('Location'), default='', max_length=255)
    geolocation = PlainLocationField(
        default='9.895804362670006,-84.1552734375', zoom=15)

    organization = TreeForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE)

    rooms = models.ManyToManyField(
        'LaboratoryRoom', verbose_name=_("Rooms"), blank=True)


    class Meta:
        verbose_name = _('Laboratory')
        verbose_name_plural = _('Laboratories')
        permissions = (
            ("view_report", _("Can see available reports")),
            ("do_report", _("Can download available reports")),
        )

    class MPTTMeta:
        order_insertion_by = ['name', ]

    def __str__(self):
        return '%s' % (self.name,)

    def __repr__(self):
        return self.__str__()


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)
    id_card = models.CharField(_('ID Card'), max_length=100)
    laboratories = models.ManyToManyField(Laboratory, verbose_name=_("Laboratories"), blank=True)

    def __str__(self):
        return '%s' % (self.user,)

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

    def __str__(self):
        return self.name

    @property
    def solute_list(self):
        return ast.literal_eval(self.solutes)

    @property
    def solution_object(self):
        from pyEQL import Solution as PySolution
        return PySolution(
            solutes=self.solute_list,
            volume=self.volume,
            temperature=self.temperature,
            pressure=self.pressure,
            pH=self.pH
        )
