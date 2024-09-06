from django.db import models
from django.db.models import Q

from auth_and_perms.models import Profile, Rol
from presentation.models import AbstractOrganizationRef


# Create your models here.
class PendingTask(AbstractOrganizationRef):
    STATUS = (
        (0, "Pending"),
        (1, "In process"),
        (2, "Finished")
    )
    description = models.TextField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS, default=0)
    profile = models.ForeignKey(Profile, on_delete=models.DO_NOTHING,
                                null=True, blank=True)
    rols = models.ManyToManyField(Rol)
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return f'{self.description} - {self.profile}'

