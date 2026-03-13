from django.db import models
from django.utils.translation import gettext_lazy as _
from tree_queries.models import TreeNode

from laboratory.models_utils import upload_files


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
    file = models.FileField(upload_to=upload_files, verbose_name=_("Regulation File"))
    country = models.CharField(max_length=50)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("order",)
        verbose_name = _("Regulation document")
        verbose_name_plural = _("Regulation documents")
