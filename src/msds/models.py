from django.db import models
from django.utils.translation import ugettext_lazy as _

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
