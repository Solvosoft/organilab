from django.contrib import admin
from .models import DangerIndication, BuilderInformation, Sustance, Label, \
    WarningClass, Component, WarningWord, Pictogram, PrudenceAdvice, \
    RecipientSize
from .utils import render_pdf_view
# Register your models here.
from django.utils.safestring import mark_safe
from django import forms
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple


def make_label_pdf(modeladmin, request, queryset):

    context = {'obj': queryset.first()}
    return render_pdf_view(request, "etiqueta",
                           'labels.html', context)


make_label_pdf.short_description = "Download Label"


class AdminLabels(admin.ModelAdmin):
    actions = [make_label_pdf]


class AdminDangerIndication(admin.ModelAdmin):
    #form = DangerIndicationForm
    filter_horizontal = ['pictograms', 'warning_class',
                         'warning_category', 'prudence_advice']

    def get_form(self, *args, **kwargs):
        form = super(AdminDangerIndication, self).get_form(*args, **kwargs)

        class MyForm(form):
            def __init__(self, *args, **kwargs):
                super(MyForm, self).__init__(*args, **kwargs)
                self.fields['warning_class'].queryset = \
                    WarningClass.objects.filter(
                    danger_type="class"
                )
                self.fields['warning_category'].queryset = \
                    WarningClass.objects.filter(
                    danger_type="category"
                )

        return MyForm


class AdminSustance(admin.ModelAdmin):
    filter_horizontal = ['components', 'danger_indications']


admin.site.register(WarningClass, DraggableMPTTAdmin)
admin.site.register(
    [BuilderInformation, RecipientSize, PrudenceAdvice, Component,
     WarningWord, Pictogram])
admin.site.register(DangerIndication, AdminDangerIndication)
admin.site.register(Sustance,  AdminSustance)
admin.site.register(Label, AdminLabels)
