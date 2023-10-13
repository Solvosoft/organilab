import datetime

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from tree_queries.models import TreeNode

from presentation.models import AbstractOrganizationRef

def upload_msds(instance, filename):
    date = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    fname, dot, extension = filename.rpartition('.')
    return f"msds/{slugify(date)}/{slugify(fname)}.{extension}"

def upload_regulation_document(instance, filename):
    date = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    fname, dot, extension = filename.rpartition('.')
    return f"regulation/{slugify(date)}/{slugify(fname)}.{extension}"

class MSDSObject(AbstractOrganizationRef):
    provider = models.CharField(_("Provider"), max_length=300)
    file = models.FileField(upload_to=upload_msds, verbose_name=_("MSDS File"),
                            validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    product = models.CharField(_("Product"), max_length=300)

    class Meta:
        ordering = ('pk',)
        verbose_name = _('MSDS Object')
        verbose_name_plural = _('MSDS Object')


class OrganilabNode(TreeNode):
    name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    icon = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="nodes/", null=True, blank=True)

    position = models.IntegerField(default=0)

    @property
    def is_leaf_node(self):
        return self.children.count() == 0

    @property
    def is_not_root_node(self):
        return self.parent is not None



    def __str__(self):
        return self.name

    class Meta:
        ordering = ["position"]



class RegulationDocument(models.Model):
    name = models.CharField(max_length=250)
    file = models.FileField(upload_to=upload_regulation_document, verbose_name=_("Regulation File"))
    country = models.CharField(max_length=50)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order',)
        verbose_name = _('Regulation document')
        verbose_name_plural = _('Regulation documents')
