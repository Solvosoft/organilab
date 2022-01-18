from django.db import models

from laboratory import catalog
from laboratory.models import Object, ShelfObject, Catalog

# Create your models here.
from django.utils.translation import ugettext_lazy as _
from academic.presentation import HTMLPresentation


class Procedure(models.Model, HTMLPresentation):
    title = models.CharField(max_length=500, verbose_name=_('Title'))
    description = models.TextField(_('Description'))

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
