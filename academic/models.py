from django.db import models
from laboratory.models import Object, ShelfObject

# Create your models here.
from django.utils.translation import ugettext_lazy as _



class Procedure(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    
    def __str__(self):
        return self.title
    class Meta:
            ordering = ('pk',)
            permissions = (
                ("view_procedure", "Can see available Procedure"),
                )

class ProcedureStep(models.Model):
    procedure = models.ForeignKey(Procedure)
    title = models.CharField(max_length=500, null=True)
    description = models.TextField(null=True)
    
    def __str__(self):
        if self.title:
            return self.title
        return str(_("No titled step"))

    class Meta:
            ordering = ('pk',)
            permissions = (
                ("view_procedurestep", "Can see available ProcedureStep"),
                )
class ProcedureRequiredObject(models.Model):
    step = models.ForeignKey(ProcedureStep)
    object = models.ForeignKey(Object)
    quantity = models.FloatField(_('Material quantity'))
    measurement_unit = models.CharField(
        _('Measurement unit'), max_length=2, choices=ShelfObject.CHOICES)
    
    def __str__(self):
        return "%s %.2f %s"%(
            self.object,
            self.quantity,
            self.get_measurement_unit_display()
            )
    class Meta:
            ordering = ('pk',)
            permissions = (
                ("view_procedurerequiredobject", "Can see available ProcedureRequiredObject"),
                )
   
class ProcedureObservations(models.Model):
    step = models.ForeignKey(ProcedureStep)
    description = models.TextField()
    
    def __str__(self):
        return self.description
    
    class Meta:
            ordering = ('pk',)
            permissions = (
                ("view_procedureobservations", "Can see available ProcedureObservations"),
                )
