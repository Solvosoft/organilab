from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from fontawesome.fields import IconField
# Create your models here.


class MSDSObject(models.Model):
    provider = models.CharField(_("Provider"), max_length=300)
    file = models.FilePathField(_("MSDS File"))
    product = models.CharField(_("Product"), max_length=300)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('MSDS Object')
        verbose_name_plural = _('MSDS Object')
        permissions = (
            ("view_msdsobject", "Can see available MSDSObject"),
        )


class OrganilabNode(MPTTModel):
    name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    icon = IconField(null=True, blank=True)
    image = models.ImageField(upload_to="nodes/", null=True, blank=True)

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']
