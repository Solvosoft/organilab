from django.contrib import admin

from sga.models import TemplateSGA, PersonalTemplateSGA, SecurityLeaf
from .models import DangerIndication, BuilderInformation, Substance, Label, \
    WarningClass, Component, WarningWord, Pictogram, PrudenceAdvice, \
    RecipientSize, Donation
from .utils import render_pdf_view
# Register your models here.
#from mptt.admin import MPTTModelAdmin
from mptt.admin import DraggableMPTTAdmin
from django.utils.translation import ugettext_lazy as _


def make_label_pdf(modeladmin, request, queryset):

    context = {'obj': queryset.first()}
    return render_pdf_view(request, "etiqueta",
                           'labels.html', context)


make_label_pdf.short_description = _("Download Label")


class AdminLabels(admin.ModelAdmin):
    actions = [make_label_pdf]


class AdminDangerIndication(admin.ModelAdmin):
    # form = DangerIndicationForm
    filter_horizontal = ['pictograms', 'warning_class',
                         'warning_category', 'prudence_advice']

    def get_form(self, *args, **kwargs):
        form = super(AdminDangerIndication, self).get_form(*args, **kwargs)

        class MyForm(form):
            def __init__(self, *args_myform, **kwargs_myform):
                super(MyForm, self).__init__(*args_myform, **kwargs_myform)
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
    filter_horizontal = ['components_sga', 'danger_indications']


class DonationAdmin(admin.ModelAdmin):
    search_fields = ['details']


admin.site.register(WarningClass, DraggableMPTTAdmin)
admin.site.register(
    [BuilderInformation, RecipientSize, PrudenceAdvice, Component,
     WarningWord, Pictogram])
admin.site.register(DangerIndication, AdminDangerIndication)
admin.site.register(Substance, AdminSustance)
admin.site.register(Label, AdminLabels)
admin.site.register(TemplateSGA)
admin.site.register(Donation, DonationAdmin)
admin.site.register(PersonalTemplateSGA)
admin.site.register(SecurityLeaf)
