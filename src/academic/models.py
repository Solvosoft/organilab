from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from academic.presentation import HTMLPresentation
from laboratory import catalog
from laboratory.models import Object, Catalog
from presentation.models import AbstractOrganizationRef


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


STATUS_CHOICES = (
    ('Eraser', _('Eraser')),
    ('In Review', _('In Review')),
    ('Finalized', _('Finalized')),
)


class MyProcedure(AbstractOrganizationRef):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('Name'))
    custom_procedure = models.ForeignKey(Procedure, blank=True, null=True, on_delete=models.CASCADE, verbose_name=_('Template'))
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


class CommentProcedureStep(models.Model):
    creator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Creator"))
    creator_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    procedure_step = models.ForeignKey(ProcedureStep, blank=True, null=True, on_delete=models.CASCADE,
                                       verbose_name=_('Step'))
    my_procedure = models.ForeignKey(MyProcedure, blank=True, null=True, on_delete=models.CASCADE,
                                     verbose_name=_('My procedure'))

    def __str__(self):
        return f'{self.creator} - {self.creator_at}'


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

