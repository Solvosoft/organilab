from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(_('Phone'), default='', max_length=25)
    id_card = models.CharField(_('ID Card'), max_length=100)
    laboratories = models.ManyToManyField('laboratory.Laboratory', verbose_name=_("Laboratories"), blank=True)
    job_position = models.CharField(_('Job Position'), max_length=100)

    def __str__(self):
        return '%s' % (self.user,)


class Rol(models.Model):
    name = models.CharField(blank=True,max_length=100)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )


    class Meta:
        verbose_name = _('Rol')
        verbose_name_plural = _('Rols')

    def __str__(self):
        return self.name


class ProfilePermission(models.Model):
    profile = models.ForeignKey(Profile, verbose_name=_("Profile"), blank=True, null=True, on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

#    laboratories = models.ForeignKey('laboratory.Laboratory', verbose_name=_("Laboratories"), blank=True, null=True, on_delete=models.CASCADE)
    rol = models.ManyToManyField(Rol, blank=True, verbose_name=_("Rol"))

    def __str__(self):
        return '%s' % (self.profile,)

    class Meta:
        verbose_name = _('Profile Rol')
        verbose_name_plural = _('Profile Rols')
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
