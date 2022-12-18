from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from academic.presentation import HTMLPresentation
from laboratory import catalog
from laboratory.models import Object, Catalog


class Procedure(models.Model, HTMLPresentation):
    title = models.CharField(max_length=500, verbose_name=_('Title'))
    description = models.TextField(_('Description'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure')
        verbose_name_plural = _('Procedures')


class ProcedureStep(models.Model, HTMLPresentation):
    procedure = models.ForeignKey(Procedure, verbose_name=_("Procedure"), on_delete=models.CASCADE)
    title = models.CharField(_('Title'), max_length=500, null=True)
    description = models.TextField(_('Description'), null=True)

    def __str__(self):
        if self.title:
            return self.title
        return str(_("No titled step"))

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure step')
        verbose_name_plural = _('Procedure steps')


class ProcedureRequiredObject(models.Model):
    step = models.ForeignKey(ProcedureStep, on_delete=models.CASCADE)
    object = models.ForeignKey(Object, verbose_name=_('Object'), on_delete=models.CASCADE)
    quantity = models.FloatField(_('Material quantity'))
    measurement_unit = catalog.GTForeignKey(Catalog,  on_delete=models.DO_NOTHING,
                             verbose_name=_('Measurement unit'), key_name="key", key_value='units')

    def get_object_detail(self):
        return "%s %s" % (self.object, str(self.measurement_unit))

    def __str__(self):
        return "%s %.2f %s" % (
            self.object,
            self.quantity,
            str(self.measurement_unit)
        )

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure Required Object')
        verbose_name_plural = _('Procedure Required Objects')


class ProcedureObservations(models.Model):
    step = models.ForeignKey(ProcedureStep, on_delete=models.CASCADE)
    description = models.TextField(_('Description'))

    def __str__(self):
        return self.description

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure Observation')
        verbose_name_plural = _('Procedure Observations')


class ComponentSGA(models.Model):
    name = models.CharField(max_length=250, verbose_name=_("Name"))
    cas_number = models.CharField(max_length=150, verbose_name=_("CAS number"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('ComponentSGA')
        verbose_name_plural = _('ComponentsSGA')


class SubstanceSGA(models.Model):
    comercial_name = models.CharField(max_length=250,
                                      verbose_name=_("Comercial name"))
    synonymous = models.TextField(verbose_name=_("Synonymous"))

    uipa_name= models.CharField(max_length=250, blank=True,
                                verbose_name=_("UIPA name"))
    components = models.ManyToManyField(
        ComponentSGA, verbose_name=_("Components"))
    agrochemical = models.BooleanField(default=False,
                                       verbose_name=_("Agrochemical"))
    is_public = models.BooleanField(default=True, verbose_name=_('Share with others'))

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_approved = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.comercial_name

    class Meta:
        verbose_name = _('SustanceSGA')
        verbose_name_plural = _('SustancesSGA')


class SustanceCharacteristicsSGA(models.Model):
    substance = models.OneToOneField(SubstanceSGA, on_delete=models.CASCADE)
    iarc = catalog.GTForeignKey(Catalog, related_name="gt_iarcrelsga", on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IARC")
    imdg = catalog.GTForeignKey(Catalog, related_name="gt_imdgsga", on_delete=models.DO_NOTHING,
                                null=True, blank=True, key_name="key", key_value="IDMG")
    white_organ = catalog.GTManyToManyField(Catalog, related_name="gt_white_organsga", key_name="key",
                                            key_value="white_organ", blank=True)
    bioaccumulable = models.BooleanField(null=True)
    molecular_formula = models.CharField(_('Molecular formula'), max_length=255, null=True, blank=True)
    cas_id_number = models.CharField(
        _('Cas ID Number'), max_length=255, null=True, blank=True)
    security_sheet = models.FileField(
        _('Security sheet'), upload_to='security_sheets/', null=True, blank=True)
    is_precursor = models.BooleanField(_('Is precursor'), default=False)
    precursor_type = catalog.GTForeignKey(Catalog, related_name="gt_precursorsga", on_delete=models.SET_NULL,
                                          null=True, blank=True, key_name="key", key_value="Precursor")

    h_code = models.ManyToManyField('sga.DangerIndication', verbose_name=_("Danger Indication"), blank=True)
    valid_molecular_formula = models.BooleanField(default=False)
    ue_code = catalog.GTManyToManyField(Catalog, related_name="gt_uesga", key_name="key",
                                        key_value="ue_code", blank=True, verbose_name=_('UE codes'))
    nfpa = catalog.GTManyToManyField(Catalog, related_name="gt_nfpasga", key_name="key",
                                     key_value="nfpa", blank=True, verbose_name=_('NFPA codes'))
    storage_class = catalog.GTManyToManyField(Catalog, related_name="gt_storage_classsga", key_name="key",
                                              key_value="storage_class", blank=True, verbose_name=_('Storage class'))
    seveso_list = models.BooleanField(verbose_name=_('Is Seveso list III?'), default=False)

    class Meta:
        verbose_name = _('Sustance characteristicSGA')
        verbose_name_plural = _('Sustance characteristicsSGA')


class SubstanceObservation(models.Model):
    substance = models.ForeignKey("sga.Substance",on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_('Description'))
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True,verbose_name=_('Creator'))
    create_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date'))

    class Meta:
        verbose_name = _('Observation')
        verbose_name_plural = _('Observations')

    def __str__(self):
        return f'{self.substance} {self.creator}'