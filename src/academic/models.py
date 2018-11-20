from django.db import models
from laboratory.models import Object, ShelfObject

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
        permissions = (
            ("view_procedure", _("Can see available Procedure")),
        )


class ProcedureStep(models.Model, HTMLPresentation):
    procedure = models.ForeignKey(Procedure, verbose_name=_("Procedure"))
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
        permissions = (
            ("view_procedurestep", _("Can see available ProcedureStep")),
        )


class ProcedureRequiredObject(models.Model):
    step = models.ForeignKey(ProcedureStep)
    object = models.ForeignKey(Object, verbose_name=_('Object'))
    quantity = models.FloatField(_('Material quantity'))
    measurement_unit = models.CharField(
        _('Measurement unit'), max_length=2, choices=ShelfObject.CHOICES)

    def __str__(self):
        return "%s %.2f %s" % (
            self.object,
            self.quantity,
            self.get_measurement_unit_display()
        )

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure Required Object')
        verbose_name_plural = _('Procedure Required Objects')
        permissions = (
            ("view_procedurerequiredobject", _(
                "Can see available ProcedureRequiredObject")),
        )


class ProcedureObservations(models.Model):
    step = models.ForeignKey(ProcedureStep)
    description = models.TextField(_('Description'))

    def __str__(self):
        return self.description

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Procedure Observation')
        verbose_name_plural = _('Procedure Observations')
        permissions = (
            ("view_procedureobservations", _(
                "Can see available ProcedureObservations")),
        )
