from django.db import models

# Create your models here.


class MSDSObject(models.Model):
    provider = models.CharField(max_length=300)
    file = models.FilePathField()
    product = models.CharField(max_length=300)

    class Meta:
        ordering = ('pk',)
        permissions = (
            ("view_msdsobject", "Can see available MSDSObject"),
        )
