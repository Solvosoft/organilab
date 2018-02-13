from django.contrib import admin
from laboratory import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group

class Object_Admin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_precursor')

class OrganizationStruture_inline(admin.TabularInline):
    model = models.OrganizationStructure
    
class Laboratory_inline(admin.TabularInline):
    model = models.Laboratory
        
class OrganizationStrutureAdmin(admin.ModelAdmin):
    fields = ('name','group')  
    search_fields = ["name"]
    inlines = [
        OrganizationStruture_inline,
    ]
    
    
class PrincipalTechnicianAdmin(admin.ModelAdmin):
    fields= ('name','id_card','phone_number','credentials')
    search_fields = ["credentials__username"]
    inlines = [
        Laboratory_inline
    ]
    list_select_related = (
        'credentials',
    )
            
admin.site.register(models.Laboratory)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.FeedbackEntry)
admin.site.register(models.Solution)



admin.site.register(models.PrincipalTechnician,PrincipalTechnicianAdmin)
admin.site.register(models.OrganizationStructure,OrganizationStrutureAdmin)




admin.site.site_header = _('Organilab Administration site')