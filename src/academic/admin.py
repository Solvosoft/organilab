from django.contrib import admin

from academic.models import SubstanceSGA, ComponentSGA, SustanceCharacteristicsSGA

# Register your models here.
admin.site.register(SubstanceSGA)
admin.site.register(SustanceCharacteristicsSGA)
admin.site.register(ComponentSGA)