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