from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class OrganizationGroup(models.Model):
    name = models.CharField(blank=True,max_length=100)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,  blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    @property
    def gt_get_permission(self):
        return self.permissions

    class Meta:
        verbose_name = _('Group Rol')
        verbose_name_plural = _('Group Rols')
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return self.name

