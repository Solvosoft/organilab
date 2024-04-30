from django.contrib import admin

from academic import models

class ProcedureAdmin(admin.ModelAdmin):
    search_fields = ['title']

admin.site.register(models.Procedure, ProcedureAdmin)
