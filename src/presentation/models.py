from django.conf import settings
from django.db import models

class AbstractOrganizationRef(models.Model):

    organization = models.ForeignKey('laboratory.OrganizationStructure', null=True, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True