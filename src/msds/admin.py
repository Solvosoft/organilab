from django.contrib import admin
from msds.models import MSDSObject, OrganilabNode, RegulationDocument
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from ckeditor_uploader.widgets import CKEditorUploadingWidget
# Register your models here.
from django.db import models


class msdsAdmin(admin.ModelAdmin):
    search_fields = ['provider', 'product']
    list_display = ['provider', 'product']


class OrganilabNodeMPTTAdmin(DraggableMPTTAdmin):
    mptt_level_indent = 20
    formfield_overrides = {
        models.TextField: {'widget': CKEditorUploadingWidget},
    }


admin.site.register(OrganilabNode, OrganilabNodeMPTTAdmin)
admin.site.register(MSDSObject, msdsAdmin)
admin.site.register(RegulationDocument)