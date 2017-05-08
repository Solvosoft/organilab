from django.contrib import admin
from laboratory import models
from django.utils.translation import ugettext_lazy as _


class Object_Admin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_precursor')

admin.site.register(models.Laboratory)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.FeedbackEntry)
admin.site.register(models.Solution)

admin.site.site_header = _('Organilab Administration site')