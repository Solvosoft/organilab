from django.contrib import admin
from laboratory import models
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin, TreeRelatedFieldListFilter
from constance.admin import ConstanceAdmin, ConstanceForm, Config

class RelatedFieldListFilter(TreeRelatedFieldListFilter):
    mptt_level_indent = 20

class Object_Admin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_precursor')

     
class PrincipalTechnician_library_inline(admin.TabularInline):
    model = models.PrincipalTechnician
    exclude = ('organization', )
 
 
class PrincipalTechnician_Organization_inline(admin.TabularInline):
    model = models.PrincipalTechnician 
    exclude = ('laboratory','assigned' )
 
class OrganizationStrutureMPTTModelAdmin(MPTTModelAdmin):
    search_fields = ["name", 'laboratories']
    list_display = ["name", 'laboratories']
    inlines = (  PrincipalTechnician_Organization_inline,)
    mptt_level_indent = 20              
         
     
class LaboratoryAdmin(admin.ModelAdmin):
    inlines = (PrincipalTechnician_library_inline, )

 
class CustomConfigForm(ConstanceForm):
    def __init__(self, *args, **kwargs):
        super(CustomConfigForm, self).__init__(*args, **kwargs)
        #... do stuff to make your settings form nice ...

class ConfigAdmin(ConstanceAdmin):
    change_list_form = CustomConfigForm


admin.site.unregister([Config])
admin.site.register([Config], ConfigAdmin)
            
admin.site.register(models.Laboratory, LaboratoryAdmin)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.FeedbackEntry)
admin.site.register(models.Solution)



admin.site.register(models.PrincipalTechnician)
admin.site.register(models.OrganizationStructure, OrganizationStrutureMPTTModelAdmin)











admin.site.site_header = _('Organilab Administration site')