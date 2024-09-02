from django.db import models
from auth_and_perms.models import Profile, Rol

# Create your models here.
class PendingTask(models.Model):
    STATUSES = (
        (0, "Pending"),
        (1, "In process"),
        (3, "Finished")
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    status = models.IntegerField(choices=STATUSES, default=0)
    validate_profile = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    rols = models.ManyToManyField(Rol, related_name='pending_tasks')
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return "%s - %s" % (self.description, self.status)
