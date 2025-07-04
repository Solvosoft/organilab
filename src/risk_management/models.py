from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from location_field.models.plain import PlainLocationField

from laboratory import catalog
from laboratory.models import Laboratory, Catalog
from laboratory.models_utils import upload_files
from presentation.models import AbstractOrganizationRef
from risk_management.models_utils import PriorityCalculator

class PriorityConstrain(AbstractOrganizationRef, PriorityCalculator):
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

class RiskZone(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_('Name'))
    laboratories = models.ManyToManyField('laboratory.Laboratory', verbose_name=_('Laboratories'))
    buildings = models.ManyToManyField('risk_management.Buildings',
                                 verbose_name=_('Buildings'))
    num_workers = models.SmallIntegerField(verbose_name=_('Number of workers (aprox)'))
    zone_type = models.ForeignKey(ZoneType, on_delete=models.CASCADE, verbose_name=_('Zone Type'))
    priority = models.SmallIntegerField(verbose_name=_('Priority'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Risk zone')
        verbose_name_plural = _('Risk zones')
        ordering = ('priority', 'pk')

def upload_notification_copy(instance, filename):
    date = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    fname, dot, extension = filename.rpartition('.')
    return f"notifications/{slugify(date)}/{slugify(fname)}.{extension}"

class IncidentReport(AbstractOrganizationRef):
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

    notification_copy = models.FileField(upload_to=upload_notification_copy,
                verbose_name=_('En caso de intoxicación adjuntar copia de la notificación realizada al Centro Nacional de Control de Intoxicaciones (CNCI)'),
                null=True, blank=True)
    buildings = models.ManyToManyField('risk_management.Buildings',
                                       verbose_name=_('Buildings'),
                                       related_name="incident_buildings",
                                       blank=True)
    risk_zone = models.ForeignKey('risk_management.RiskZone',
                                       verbose_name=_('Risk Zone'),
                                       null=True, blank=True,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return self.short_description

class Regent(AbstractOrganizationRef):
    TYPEREGENTS = (
        ("chemical", _("Chemical")),
        ("chemical_engineer", _("Chemical Engineer")),
        ("veterinarian", _("Veterinarian")),
    )

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             related_name="regent_user")
    laboratories = models.ManyToManyField(Laboratory, related_name="regent_laboratories")
    type_regent =  models.CharField(max_length=100, choices=TYPEREGENTS,
                                    default="chemical", verbose_name=_("Type Regent"))

    class Meta:
        ordering = ['pk']


    def __str__(self):
        return self.user.username

class Buildings(AbstractOrganizationRef):
    name = models.CharField(verbose_name=_("Name"),
                            max_length=255, null=False,
                            blank=False)
    laboratories = models.ManyToManyField(Laboratory,
                                          verbose_name=_("Laboratories"),
                                          related_name="buildings",
                                          blank=True)
    is_asociaty_buildings = models.BooleanField(
        verbose_name=_("It is Associated with Buildings?"),
                                                default=False)
    nearby_buildings = models.ManyToManyField("self",
                                              symmetrical=False,
                                              verbose_name=_("Nearby Buildings"),
                                              related_name="near_buildings_as",
                                              blank=True)
    phone = models.CharField(verbose_name=_("Phone"),
                             max_length=25, null=False, blank=False)
    manager = models.ForeignKey(User, verbose_name=_("Responsible"),
                                related_name="manager",null=True, blank=True,
                                on_delete=models.DO_NOTHING)
    geolocation = PlainLocationField(
        default='9.895804362670006,-84.1552734375', zoom=15)
    regents = models.ManyToManyField("risk_management.Regent",
                                               verbose_name=_("Regents Associated"),
                                               related_name="regents",
                                     blank=True)
    has_water_resources = models.BooleanField(verbose_name=_("Presence of rivers, "
                                                             "streams, springs and "
                                                             "aquifers"),
                                              default=False)
    has_nearby_sites = models.FileField(verbose_name=_("Are there establishments with a "
                                                       "large concentration of people "
                                                       "that could be exposed to the "
                                                       "risk of an accident?"),
                                        upload_to=upload_files,
                                        null=True,
                                        blank=True)
    area = models.FloatField(verbose_name=_("Area"), default=0.0)
    plans = models.FileField(verbose_name=_("Plans"),
                             upload_to=upload_files,
                             null=True, blank=True)
    security_plan = models.FileField(verbose_name=_("Security Plan"),
                                     upload_to=upload_files,
                                     null=True, blank=True)
    regulatory_plans = models.FileField(verbose_name=_("Regulatory Plans"),
                                     upload_to=upload_files,
                                     null=True, blank=True)
    emergency_plan = models.FileField(verbose_name=_("Emergency Plan"),
                                     upload_to=upload_files,
                                     null=True, blank=True)

    class Meta:
        ordering = ['pk']


    def __str__(self):
        return self.name

class Structure(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_('Name'), null=False,
                            blank=False)
    buildings = models.ManyToManyField('risk_management.Buildings',
                                       verbose_name=_('Buildings'),
                                       related_name="structura_buildings")
    type_structure = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING,
                                verbose_name=_('Type'),
                                key_name="key", key_value='structure_type')
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Area'))
    measuerement_unit = catalog.GTForeignKey(Catalog, on_delete=models.DO_NOTHING,
                                verbose_name=_('Measurement Unit'),
                                key_name="key", key_value='distance_unit',
                                             related_name="structure_measurement_unit")
    geolocation = PlainLocationField(default='9.895804362670006,-84.1552734375',
                                     zoom=15, verbose_name=_('Geolocation'))
    manager = models.ForeignKey(User, verbose_name=_('Responsible'),
                                on_delete=models.DO_NOTHING, related_name="structure_manager")
    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.name
