import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.expressions import F
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from location_field.models.plain import PlainLocationField
from tree_queries.fields import TreeNodeForeignKey
from tree_queries.models import TreeNode
from tree_queries.query import TreeQuerySet
from django.db.models import Sum, Q
from organilab.settings import DATE_INPUT_FORMATS
from presentation.models import AbstractOrganizationRef
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
    name = models.CharField(_('Name'), max_length=250, unique=True)
    description = models.TextField(_('Description'))

    class Meta:
        verbose_name = _('Object feature')
        verbose_name_plural = _('Object features')

    def __str__(self):
        return self.name


class Object(AbstractOrganizationRef):
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
    type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES, default=REACTIVE)
    is_public = models.BooleanField(default=True, verbose_name=_('Share with others'))
    description = models.TextField(_('Description'), null=True, blank=True)

    features = models.ManyToManyField(ObjectFeatures, verbose_name=_("Object features"))

    model = models.CharField(_('Model'), max_length=50, null=True, blank=True)
    serie = models.CharField(_('Serie'), max_length=50, null=True, blank=True)
    plaque = models.CharField(
        _('Plaque'), max_length=50, null=True, blank=True)

    @property
    def is_reactive(self):
        return self.type == self.REACTIVE

    @property
    def is_precursor(self):
        if hasattr(self, 'sustancecharacteristics') and self.sustancecharacteristics:
            return self.sustancecharacteristics.is_precursor
        return False

    @property
    def cas_code(self):
        if hasattr(self, 'sustancecharacteristics') and self.sustancecharacteristics:
            return self.sustancecharacteristics.cas_id_number
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
    white_organ = catalog.GTManyToManyField(Catalog, related_name="gt_white_organ", key_name="key",
                                            key_value="white_organ", blank=True)
    bioaccumulable = models.BooleanField(null=True)
    molecular_formula = models.CharField(_('Molecular formula'), max_length=255, null=True, blank=True)
    cas_id_number = models.CharField(
        _('Cas ID Number'), max_length=255, null=True, blank=True)
    security_sheet = models.FileField(
        _('Security sheet'), upload_to='security_sheets/', null=True, blank=True)
    is_precursor = models.BooleanField(_('Is precursor'), default=False)
    precursor_type = catalog.GTForeignKey(Catalog, related_name="gt_precursor", on_delete=models.SET_NULL,
                                          null=True, blank=True, key_name="key", key_value="Precursor")

    h_code = models.ManyToManyField('sga.DangerIndication', verbose_name=_("Danger Indication"), blank=True)
    valid_molecular_formula = models.BooleanField(default=False)
    ue_code = catalog.GTManyToManyField(Catalog, related_name="gt_ue", key_name="key",
                                        key_value="ue_code", blank=True, verbose_name=_('UE codes'))
    nfpa = catalog.GTManyToManyField(Catalog, related_name="gt_nfpa", key_name="key",
                                     key_value="nfpa", blank=True, verbose_name=_('NFPA codes'))
    storage_class = catalog.GTManyToManyField(Catalog, related_name="gt_storage_class", key_name="key",
                                              key_value="storage_class", blank=True, verbose_name=_('Storage class'))
    seveso_list = models.BooleanField(verbose_name=_('Is Seveso list III?'), default=False)
    img_representation = models.ImageField(upload_to='sustances/', verbose_name=_('Sustance representation'),
                                           null=True, blank=True)

    class Meta:
        verbose_name = _('Sustance characteristic')
        verbose_name_plural = _('Sustance characteristics')


class ShelfObject(models.Model):
    shelf = models.ForeignKey('Shelf', verbose_name=_("Shelf"), on_delete=models.CASCADE)
    object = models.ForeignKey('Object', verbose_name=_(
        "Equipment or reactive or sustance"), on_delete=models.CASCADE)
    quantity = models.FloatField(_('Material quantity'), help_text='Use dot like 0.344 on decimal')
    limit_quantity = models.FloatField(_('Limit material quantity'), help_text='Use dot like 0.344 on decimal')
    measurement_unit = catalog.GTForeignKey(Catalog, related_name="measurementunit", on_delete=models.DO_NOTHING,
                                            verbose_name=_('Measurement unit'), key_name="key", key_value='units')
    in_where_laboratory = models.ForeignKey('Laboratory', null=True, blank=False, on_delete=models.CASCADE)
    marked_as_discard = models.BooleanField(default=False)
    laboratory_name = models.CharField(null=True, blank=True, verbose_name=_('Laboratory name'), max_length=30)
    course_name = models.CharField(null=True, blank=True, verbose_name=_('Course name'), max_length=30)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, null=True, blank=True, verbose_name=_('Creator'), on_delete=models.CASCADE)

    shelf_object_url = models.TextField(null=True, verbose_name=_("Shelf Object Url"))
    shelf_object_qr = models.FileField(null=True, verbose_name=_('Shelf Object QR'), upload_to='shelf_object_qr/')

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

    def get_object_detail(self):
        return '%s %s %s %s' %(self.object.code, self.object.name, self.quantity, str(self.measurement_unit))

class LaboratoryRoom(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

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
    type = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING, verbose_name=_('Type'),
                                key_name="key", key_value='container_type')
    color = models.CharField(default="#73879C", max_length=10)
    discard = models.BooleanField(default=False,verbose_name=_('Disposal'))
    quantity = models.FloatField(default=0,verbose_name=_('Quantity'), help_text='Use dot like 0.344 on decimal')
    measurement_unit = catalog.GTForeignKey(Catalog, null=True, blank=True, related_name="measurementshelfunit", on_delete=models.DO_NOTHING,
                                            verbose_name=_('Measurement unit'), key_name="key", key_value='units')
    description= models.TextField(null=True,blank=True, default="", verbose_name=_('Description'))
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

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

    def get_shelf(self):
        return '%s %s %s %s' % (self.furniture.labroom.name, self.furniture.name, str(self.type), self.name)


    def get_total_refuse(self):
        return ShelfObject.objects.filter(shelf=self).aggregate(amount = Sum('quantity', default=0))['amount']

    def get_refuse_porcentage(self):
        result=0
        try:
            result=(self.get_total_refuse()/self.quantity)*100
        except ZeroDivisionError:
            result=0
        return result

    def get_measurement_unit_display(self):
        return str(self.measurement_unit) if self.measurement_unit else _('Unknown')

    def __str__(self):
        return '%s %s %s' % (self.furniture, str(self.type), self.name)


    class Meta:
        permissions = [('can_manage_disposal', 'Can manage disposal'),
                       ('can_add_disposal', 'Can add disposal'),
                       ('can_view_disposal', 'Can view disposal')]

class Furniture(models.Model):
    labroom = models.ForeignKey('LaboratoryRoom', on_delete=models.CASCADE, verbose_name=_("Labroom"))
    name = models.CharField(_('Name'), max_length=255)
    # old  'F' Cajón   'D' Estante
    type = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING, verbose_name=_('Type'),
                                key_name="key", key_value='furniture_type')
    color = models.CharField(default="#73879C", max_length=10)
    dataconfig = models.TextField(_('Data configuration'))

    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

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

    def get_limited_shelf_objects(self):
        return ShelfObject.objects.filter(shelf__furniture=self,quantity__lte=F('limit_quantity'))

    def __str__(self):
        return '%s' % (self.name)


class OrganizationStructureManager(models.Manager):

    def filter_user(self, user, descendants=True, include_self=True, ancestors=False, org_pk=None):
        qparams = Q(pk__in=user.userorganization_set.values_list('organization', flat=True))|Q(
            organizationusermanagement__users=user)
        if org_pk:
            organizations = OrganizationStructure.objects.filter(pk=org_pk).filter(qparams)
        else:
            organizations = OrganizationStructure.objects.filter(qparams)

        pks = []
        for org in organizations:
            if descendants:
                pks += list(org.descendants(include_self=include_self).values_list('pk', flat=True))
            if ancestors:
                pks += list(org.ancestors(include_self=include_self).values_list('pk', flat=True))
        if pks:
            return OrganizationStructure.objects.filter(pk__in=pks)
        return OrganizationStructure.objects.none()

    def get_children(self, org_id):
        return OrganizationStructure.objects.filter(pk=org_id).descendants(include_self=True)

    def filter_user_org(self, user, descendants=True, include_self=True, ancestors=False):
        # TODO: we have problems detecting user organizations
        # user.userorganization_set.all()


        organizations = OrganizationStructure.objects.filter(
            Q(organizationusermanagement__users=user)|Q(pk__in=user.userorganization_set.values_list('organization', flat=True)))
        pks = []
        for org in organizations:
            pks.append(org.pk)
            if descendants:
                for sons in org.descendants(include_self=include_self).filter(organizationusermanagement__users=user):
                    if sons.pk not in pks:
                        pks.append(sons.pk)

            if ancestors:
                for parent in org.descendants(include_self=include_self).filter(organizationusermanagement__users=user):
                    if parent.pk not in pks:
                        pks.append(parent.pk)

        if pks:

            return OrganizationStructure.objects.filter(pk__in=pks)

        return OrganizationStructure.objects.none()

    def filter_user_orgs(self, user, org=None, descendants=True, include_self=True, ancestors=False):
        organizations = OrganizationStructure.objects.filter(organizationusermanagement__users=user,organizationusermanagement__organization=org)
        pks = []
        for org in organizations:
            pks.append(org.pk)
            if descendants:
                for sons in org.descendants(include_self=include_self).filter(organizationusermanagement__users=user):
                    if sons.pk not in pks:
                        pks.append(sons.pk)

            if ancestors:
                for parent in org.descendants(include_self=include_self).filter(organizationusermanagement__users=user):
                    if parent.pk not in pks:
                        pks.append(parent.pk)

        if pks:

            return OrganizationStructure.objects.filter(pk__in=pks)

        return OrganizationStructure.objects.none()

    def filter_labs_by_user(self, user, org_pk=None):
        contenttype = ContentType.objects.filter(app_label='laboratory', model='laboratory').first()

        orgs = self.filter_user(user, descendants=True, include_self=True, ancestors=True, org_pk=org_pk)
        labs_related = set(OrganizationStructureRelations.objects.filter(
            organization__in = orgs,
            content_type = contenttype,
        ).values_list('object_id', flat=True))
        labs_in_orgs = set(orgs.exclude(laboratory=None).values_list('laboratory', flat=True))

        pks = labs_related.union(labs_in_orgs)
        return contenttype.model_class().objects.filter(pk__in=pks)

class OrganizationStructure(TreeNode):
    name = models.CharField(_('Name'), max_length=255)
    position = models.IntegerField(default=0)
    # No debe usarse para validar permisos, su intención es permitir relacionarlos en la
    # vista de administración, para los permisos usar ProfilePermission
    rol = models.ManyToManyField('auth_and_perms.Rol', blank=True)
    level = models.SmallIntegerField(default=0)
    objects = TreeQuerySet.as_manager()
    os_manager = OrganizationStructureManager()

    class Meta:
        ordering = ["position"]
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        permissions = (
            ('add_organizationusermanagement', _('Can add organization user management')),
            ('change_organizationusermanagement', _('Can change organization user management')),
            ('delete_organizationusermanagement', _('Can delete organization user management')),
            ('view_organizationusermanagement', _('Can view organization user management')),
        )

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
    organization = models.ForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE)
    users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return "%s" % self.organization.name


class OrganizationStructureRelations(models.Model):
    organization = models.ForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class Laboratory(models.Model):
    name = models.CharField(_('Laboratory name'), default='', max_length=255)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)

    location = models.CharField(_('Location'), default='', max_length=255)
    geolocation = PlainLocationField(
        default='9.895804362670006,-84.1552734375', zoom=15)
    email= models.EmailField(_('Email'),blank=True)
    coordinator=models.CharField(_('Coordinator'), default='', max_length=255, blank=True)
    unit=models.CharField(_('Unit'), default='', max_length=50, blank=True)
    organization = TreeNodeForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE, null=True)

    rooms = models.ManyToManyField(
        'LaboratoryRoom', verbose_name=_("Rooms"), blank=True)

    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Laboratory')
        verbose_name_plural = _('Laboratories')
        permissions = (
            ("view_report", _("Can see available reports")),
            ("do_report", _("Can download available reports")),
        )

    def __str__(self):
        return '%s' % (self.name,)

    def __repr__(self):
        return self.__str__()


class Provider(models.Model):
    name = models.CharField(max_length=255, blank=True, default='',verbose_name=_('Name'))
    phone_number = models.CharField(max_length=25, blank=True, default='',verbose_name=_('Phone'))
    email = models.EmailField(blank=True,verbose_name=_('Email'))
    legal_identity = models.CharField(max_length=50,blank=True,default='',verbose_name=_('legal identity'))
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE,blank=True, null=True)

    def __str__(self):
        return self.name


class ObjectLogChange(models.Model):
    object = models.ForeignKey(Object, db_constraint=False, on_delete=models.DO_NOTHING)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    user = models.ForeignKey(User, db_constraint=False, on_delete=models.DO_NOTHING)
    old_value = models.FloatField(default=0)
    new_value = models.FloatField(default=0)
    diff_value = models.FloatField(default=0)
    update_time = models.DateTimeField(auto_now_add=True)
    precursor = models.BooleanField(default=False)
    measurement_unit = catalog.GTForeignKey(Catalog, related_name="logmeasurementunit", on_delete=models.DO_NOTHING,
                                            verbose_name=_('Measurement unit'), key_name="key", key_value='units')
    subject = models.CharField(max_length=100, blank=True, null=True)
    provider= models.ForeignKey(Provider, blank=True, db_constraint=False, on_delete=models.DO_NOTHING, null=True)
    bill = models.CharField(max_length=100, blank=True, null=True)
    type_action=models.IntegerField(default=0)
    note = models.CharField(default='',blank=True, null=True, max_length=255)

    def __str__(self):
        return self.object.name

class BlockedListNotification(models.Model):
    laboratory = models.ForeignKey(
        Laboratory, on_delete=models.CASCADE, verbose_name=_("Laboratory"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    object = models.ForeignKey(Object, on_delete=models.CASCADE, verbose_name=_("Object"))

    class Meta:
        verbose_name = _('Blocked List Notification')
        verbose_name_plural = _('Bloked List Notifications')
    
    def __str__(self):
        return f"{self.object}: {self.laboratory}: {self.user}"

REQUESTED = 0
ACCEPTED = 1


TRANFEROBJECT_STATUS = (
    (REQUESTED, _("Requested")),
    (ACCEPTED, _("Accepted")),
)

class TranferObject(models.Model):
    object = models.ForeignKey(ShelfObject, on_delete=models.CASCADE,verbose_name=_("Object"))
    laboratory_send = models.ForeignKey(Laboratory, on_delete=models.CASCADE, verbose_name=_("Laboratory Send"), related_name="lab_send")
    laboratory_received = models.ForeignKey(Laboratory, on_delete=models.CASCADE, verbose_name=_("Laboratory Received"), related_name="lab_received")
    quantity = models.FloatField()
    update_time = models.DateTimeField(auto_now_add=True)
    state = models.BooleanField(default=True)
    status = models.SmallIntegerField(choices=TRANFEROBJECT_STATUS, default=REQUESTED)
    mark_as_discard = models.BooleanField(default=False)

    def get_object_detail(self):
        return "%s %s %s" % (self.object.object.name, self.quantity, str(self.object.measurement_unit))

MONTHS=(
    (1, _('January')),
    (2, _('February')),
    (3, _('March')),
    (4, _('April')),
    (5, _('May')),
    (6, _('June')),
    (7, _('July')),
    (8, _('August')),
    (9, _('September')),
    (10, _('October')),
    (11, _('November')),
    (12, _('December')),
)

class PrecursorReport(models.Model):
    month = models.IntegerField(choices=MONTHS)
    year = models.IntegerField()
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, verbose_name=_('Laboratory'))
    consecutive = models.IntegerField(default=1)


STATUS_CHOICES = (
    (_('Eraser'), _('Eraser')),
    (_('In Review'), _('In Review')),
    (_('Finalized'), _('Finalized')),
)


class Inform(AbstractOrganizationRef):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('Name'))
    custom_form = models.ForeignKey('derb.CustomForm', blank=True, null=True, on_delete=models.CASCADE,verbose_name=_('Template'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    context_object = GenericForeignKey('content_type', 'object_id')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Eraser')
    schema = models.JSONField(default=dict)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class CommentInform(models.Model):
    creator = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, verbose_name=_("Creator"))
    create_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    inform = models.ForeignKey(Inform, blank=True, null=True, on_delete=models.CASCADE, verbose_name=_('Inform'))

    def __str__(self):
        return f'{self.creator} - {self.create_at}'


class LabOrgLogEntry(models.Model):
    log_entry = models.ForeignKey('admin.LogEntry', on_delete=models.CASCADE, verbose_name=_("Log Entry"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'{self.log_entry}'


class Protocol(models.Model):
    name = models.CharField(_("Name"), max_length=300)
    file = models.FileField(upload_to="protocols", verbose_name=_("Protocol PDF File"),
                            validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    short_description = models.CharField(_("short description"), max_length=300)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    upload_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Protocol')
        verbose_name_plural = _('Protocols')

class UserOrganization(models.Model):
    organization = models.ForeignKey(
        OrganizationStructure, verbose_name=_("Organization"), on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)

    def __str__(self):
        return "%s" % self.user

    class Meta:
        ordering = ('pk',)
        verbose_name = _('User Organization')
        verbose_name_plural = _('User Organizations')


class InformScheduler(AbstractOrganizationRef):
    name = models.CharField(max_length=512)
    start_application_date = models.DateField()
    close_application_date = models.DateField()

    period_on_days = models.IntegerField(default=365)
    inform_template = models.ForeignKey('derb.CustomForm', verbose_name=_("Inform template"),  on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def last_execution(self):
        return self.informsperiod_set.order_by('start_application_date').last()


class InformsPeriod(models.Model):
    scheduler = models.ForeignKey(InformScheduler, on_delete=models.SET_NULL, null=True)
    organization = models.ForeignKey(OrganizationStructure, verbose_name=_("Organization"),
                                     on_delete=models.CASCADE)

    inform_template = models.ForeignKey('derb.CustomForm', verbose_name=_("Inform template"),
                                        on_delete=models.CASCADE)
    informs = models.ManyToManyField(Inform, blank=True)
    creation_date = models.DateField(auto_now_add=True)
    start_application_date = models.DateField()
    close_application_date = models.DateField()

    def __str__(self):
        return "%s %s to %s"%(
                self.inform_template.name,
                self.start_application_date,
                self.close_application_date)

    class Meta:
        ordering = ['-start_application_date']


class RegisterUserQR(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name=_("Created by"))
    activate_user = models.BooleanField(default=True, verbose_name=_('Activate user'))
    url = models.TextField(verbose_name=_("Url"))
    register_user_qr = models.FileField(_('Register user QR'), upload_to='register_user_qr/')
    role = models.ForeignKey('auth_and_perms.Rol', on_delete=models.DO_NOTHING, verbose_name=_('Role'))

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    organization_creator = models.ForeignKey(OrganizationStructure, on_delete=models.CASCADE, related_name='organization_creator')
    organization_register = models.ForeignKey(OrganizationStructure, on_delete=models.CASCADE, related_name='organization_register')

    code = models.CharField(max_length=4, unique=True, null=True, verbose_name=_("Code"))

    def __str__(self):
        return f"{self.url}"