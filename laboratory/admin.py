from django.contrib import admin
from laboratory import models

admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object)
admin.site.register(models.ShelfObject)
