from django.contrib import admin
from django import forms
from laboratory import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from mptt.admin import MPTTModelAdmin

class Object_Admin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_precursor')

    
class PrincipalTechnician_library_inline(admin.TabularInline):
      model = models.PrincipalTechnician
      exclude = ('organization', )


class PrincipalTechnician_Organization_inline(admin.TabularInline):
      model = models.PrincipalTechnician 
      exclude = ('laboratory', )

class OrganizationStrutureMPTTModelAdmin(MPTTModelAdmin):
    # specify pixel amount for this ModelAdmin only:
    mptt_level_indent = 20              
        
class OrganizationStrutureAdmin(admin.ModelAdmin):
    fields = ('name','group','father')  
    search_fields = ["name"]
    inlines = (  PrincipalTechnician_Organization_inline,)

    
class LaboratoryAdmin(admin.ModelAdmin):
    fields= ('name','phone_number','location','geolocation')
    inlines = (PrincipalTechnician_library_inline, )

            
admin.site.register(models.Laboratory,LaboratoryAdmin)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.FeedbackEntry)
admin.site.register(models.Solution)



admin.site.register(models.PrincipalTechnician)
admin.site.register(models.OrganizationStructure,OrganizationStrutureAdmin)




admin.site.site_header = _('Organilab Administration site')