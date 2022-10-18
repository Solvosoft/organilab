from django.db import models


class OrganizationGroup(models.Model):
    name = models.CharField(max_length=250)
