from django.db import models
from django.utils.translation import ugettext_lazy as _
from risk_management.models_utils import PriorityCalculator

class PriorityConstrain(models.Model, PriorityCalculator):
    OPERATIONS = (
        ('<', '<'),
        ('<=', '<='),
        ('=', '='),
        ('>', '>'),
        ('>=', '>='),
        ('!', '!'),
        ('<>', '<X>'),
        ('=<>=', '=<X>='),
        ('<>=', '<X>='),
        ('=<>', '=<X>'),
        ('<<', '<X<'),
        ('=<<=', '=<X<='),
        ('<<=', '<X<='),
        ('=<<', '=<X<'),
    )
    operation = models.CharField(max_length=5, choices=OPERATIONS, verbose_name=_('Opertation'))
    left_value = models.IntegerField(help_text=_('left_value opertation X ej.  left_value > 100'), verbose_name=_('Comparative value'))
    right_value = models.IntegerField(null=True, blank=True, help_text=_('Use only if =<x>=, <x>, <x>= or =<x>  '))
    priority = models.IntegerField(default=1, verbose_name=_('Set priority if true'), help_text=_('Value result if operation is True'))

    def __str__(self):
        if self.operation in ['<>', '=<>=', '<>=', '=<>', '<<', '=<<=', '<<=', '=<<']:
            right = ''
            if self.right_value:
                right = str(self.right_value)
            return "%d %s  %s --> %s" % (self.left_value, self.get_operation_display(), right, self.priority)
        return "%d %s X --> %s"%(self.left_value, self.operation, self.priority)

class ZoneType(models.Model):
    name = models.CharField(max_length=250, verbose_name=_('Name'))
    priority_validator = models.ManyToManyField(PriorityConstrain, verbose_name=_('Priority calculate operators'))

    def get_priority(self, value):
        for instance in self.priority_validator.all():
            if instance.operate(value):
                return instance.priority
        return 1

    def __str__(self):
        return self.name

class RiskZone(models.Model):
    name = models.CharField(max_length=150, verbose_name=_('Name'))
    laboratories = models.ManyToManyField('laboratory.Laboratory', verbose_name=_('Laboratories'))
    num_workers = models.SmallIntegerField(verbose_name=_('Number of workers (aprox)'))
    zone_type = models.ForeignKey(ZoneType, on_delete=models.CASCADE)
    priority = models.SmallIntegerField(verbose_name=_('Priority'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Risk zone')
        verbose_name_plural = _('Risk zones')
        ordering = ('priority', 'pk')

class IncidentReport(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    short_description = models.CharField(max_length=500, verbose_name=_("Descipción corta"),
                                         help_text=_('Descipción corta de evento, max 500 caracteres'))
    incident_date = models.DateField(verbose_name=_('Fecha del incidente'))
    laboratories = models.ManyToManyField('laboratory.Laboratory', verbose_name=_('Laboratories'))

    causes = models.TextField(
        verbose_name=_('Causas del accidente')
    )
    infraestructure_impact = models.TextField(
        verbose_name=_('Impacto a la infraestructura'),
        help_text=_('Indicando las consecuencias a corto, mediano y largo plazo.')
    )
    people_impact = models.TextField(
        verbose_name=_('Impacto a las personas (empleados, visitantes y comunidad afectada)'),
        help_text=_('Indicando las consecuencias a corto, mediano y largo plazo.')
    )
    environment_impact = models.TextField(
        verbose_name=_('Impacto ambiental'),
        help_text=_('Indicando las consecuencias a corto, mediano y largo plazo.')
    )
    result_of_plans = models.TextField(
        verbose_name=_('Resultado de la implementación del Plan de Prevención, Preparación y Respuesta ante Accidentes Químicos.')
    )

    mitigation_actions = models.TextField(
        verbose_name=_('Medidas adoptadas para corregir la situación y para atenuar sus efectos.')
    )

    recomendations = models.TextField(
        verbose_name=_('Recomendaciones'),
        help_text=_('''Recomendaciones que describan en detalle las medidas que se vayan a llevar a cabo para reducir el riesgo de que accidentes similares vuelvan a producirse.''')
    )

    notification_copy = models.FileField(upload_to='notifications/',
                verbose_name=_('En caso de intoxicación adjuntar copia de la notificación realizada al Centro Nacional de Control de Intoxicaciones (CNCI)'),
                null=True, blank=True)

    def __str__(self):
        return self.short_description