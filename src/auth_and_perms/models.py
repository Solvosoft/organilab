import random

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)
    id_card = models.CharField(_('ID Card'), max_length=100)
    laboratories = models.ManyToManyField('laboratory.Laboratory', verbose_name=_("Laboratories"), blank=True)
    job_position = models.CharField(_('Job Position'), max_length=100)

    def __str__(self):
        name = self.user.get_full_name()
        if name:
            return name
        return '%s' % (self.user,)


def get_random_color():
    hexadecimal = "#" + ''.join([random.choice('ABCDEF0123456789') for i in range(6)])
    return hexadecimal


class Rol(models.Model):
    name = models.CharField(blank=True, max_length=100)
    color = models.CharField(max_length=20, default=get_random_color)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )

    def __str__(self):
        return f'{self.pk} {self.name}'

    class Meta:
        verbose_name = _('Rol')
        verbose_name_plural = _('Rols')


class ProfilePermission(models.Model):
    profile = models.ForeignKey(Profile, verbose_name=_("Profile"), blank=True, null=True, on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    rol = models.ManyToManyField(Rol, blank=True, verbose_name=_("Rol"))

    def __str__(self):
        return '%s' % (self.profile,)

    class Meta:
        verbose_name = _('Profile Rol')
        verbose_name_plural = _('Profile Rols')
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


identification_validator = RegexValidator(
    r'"(^[1|5]\d{11}$)|(^\d{2}-\d{4}-\d{4}$)"',
    message="Debe tener el formato 08-8888-8888 para nacionales o 500000000000 o 100000000000")


class AuthenticateDataRequest(models.Model):
    identification = models.CharField(null=True,
        max_length=15, validators=[identification_validator],
        help_text="""'%Y-%m-%d %H:%M:%S',   es decir  '2006-10-25 14:30:59'""")
    # '%Y-%m-%d %H:%M:%S',   es decir  '2006-10-25 14:30:59'
    request_datetime = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=20, default='N/D')

    STATUS = ((0, 'Solicitud recibida correctamente'),
              (1, 'Ha ocurrido algún problema al solicitar la firma'),
              (2, 'Solicitud con campos incompletos'),
              (3, 'Diferencia de hora no permitida entre cliente y servidor'),
              (4, 'La entidad no se encuentra registrada'),
              (5, 'La entidad se encuentra en estado inactiva'),
              (6, 'La URL no pertenece a la entidad solicitante'),
              (7, 'El tamaño de hash debe ser entre 1 y 130 caracteres'),
              (8, 'Algoritmo desconocido'),
              (9, 'Certificado incorrecto'))
    status = models.IntegerField(choices=STATUS, default=1)
    sign_document = models.TextField(null=True, blank=True)
    response_datetime = models.DateTimeField(auto_now=True)
    # expiration_datetime = models.DateTimeField()
    id_transaction = models.IntegerField(default=0, db_index=True)
    duration = models.SmallIntegerField(default=3)
    received_notification = models.BooleanField(default=False)

    class Meta:
        ordering = ('request_datetime',)


class RegistrationUser(models.Model):
    expired_date = models.DateTimeField()
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_method = models.IntegerField(choices=((1, 'OTPT' ),(2, 'Digital Signature')), default=1)
    organization_name = models.CharField(max_length=250)


class UserTOTPDevice(models.Model):
    """
        This code will ve a string create with ID_USER and ID_TOTPDevice
        Este código va ser una cadena representada por el ID_USER y el ID_TOTPDevice
    """
    code = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    totp_device = models.ForeignKey(TOTPDevice, on_delete=models.DO_NOTHING)


class AuthorizedApplication(models.Model):
    name = models.CharField(max_length=150, unique=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    notification_url = models.URLField()
    token = models.TextField()