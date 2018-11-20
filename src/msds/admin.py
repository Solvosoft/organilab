from django.contrib import admin
from msds.models import MSDSObject, OrganilabNode
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from ckeditor.widgets import CKEditorWidget
# Register your models here.
from django.db import models


class msdsAdmin(admin.ModelAdmin):
    search_fields = ['provider', 'product']
    list_display = ['provider', 'product']


class OrganilabNodeMPTTAdmin(DraggableMPTTAdmin):
    mptt_level_indent = 20
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget},
    }


admin.site.register(OrganilabNode, OrganilabNodeMPTTAdmin)
admin.site.register(MSDSObject, msdsAdmin)
