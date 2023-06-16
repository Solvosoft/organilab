from django.contrib import admin

from sga.models import TemplateSGA, DisplayLabel, SecurityLeaf, SGAComplement, ReviewSubstance
from .models import DangerIndication, BuilderInformation, Substance, Label, \
    WarningClass, Component, WarningWord, PrudenceAdvice, \
    RecipientSize, SubstanceSGA, SustanceCharacteristicsSGA, ComponentSGA


class AdminDangerIndication(admin.ModelAdmin):
    # form = DangerIndicationForm
    filter_horizontal = ['warning_class',
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


admin.site.register(WarningClass)
admin.site.register([BuilderInformation, RecipientSize, PrudenceAdvice, Component, WarningWord])
admin.site.register(DangerIndication, AdminDangerIndication)
admin.site.register(Substance, AdminSustance)
admin.site.register(Label)
admin.site.register(TemplateSGA)
admin.site.register(DisplayLabel)
admin.site.register(SecurityLeaf)
admin.site.register(SGAComplement)
admin.site.register(ReviewSubstance)
admin.site.register(SubstanceSGA)
admin.site.register(SustanceCharacteristicsSGA)
admin.site.register(ComponentSGA)
